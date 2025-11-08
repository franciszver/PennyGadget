import { CognitoUserPool, CognitoUser, AuthenticationDetails } from 'amazon-cognito-identity-js';

// Get Cognito configuration from environment variables
const USER_POOL_ID = import.meta.env.VITE_COGNITO_USER_POOL_ID || '';
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID || '';
const REGION = import.meta.env.VITE_COGNITO_REGION || 'us-east-1';

// Create user pool instance
const poolData = {
  UserPoolId: USER_POOL_ID,
  ClientId: CLIENT_ID,
};

let userPool = null;
if (USER_POOL_ID && CLIENT_ID) {
  userPool = new CognitoUserPool(poolData);
}

/**
 * Sign up a new user
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {Object} attributes - Additional user attributes (e.g., { name: 'John Doe' })
 * @returns {Promise<Object>} Signup result
 */
export async function signUp(email, password, attributes = {}) {
  if (!userPool) {
    throw new Error('Cognito is not configured. Please set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID');
  }

  return new Promise((resolve, reject) => {
    const attributeList = [
      { Name: 'email', Value: email },
    ];

    // Add custom attributes if provided
    if (attributes.name) {
      attributeList.push({ Name: 'name', Value: attributes.name });
    }

    userPool.signUp(email, password, attributeList, null, (err, result) => {
      if (err) {
        reject(err);
        return;
      }
      resolve({
        user: result.user,
        userConfirmed: result.userConfirmed,
        codeDeliveryDetails: result.codeDeliveryDetails,
      });
    });
  });
}

/**
 * Sign in a user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<Object>} Authentication result with tokens
 */
export async function signIn(email, password) {
  if (!userPool) {
    throw new Error('Cognito is not configured. Please set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID');
  }

  return new Promise((resolve, reject) => {
    const authenticationDetails = new AuthenticationDetails({
      Username: email,
      Password: password,
    });

    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: (result) => {
        resolve({
          accessToken: result.getAccessToken().getJwtToken(),
          idToken: result.getIdToken().getJwtToken(),
          refreshToken: result.getRefreshToken().getToken(),
          user: {
            email: result.getIdToken().payload.email,
            sub: result.getIdToken().payload.sub,
          },
        });
      },
      onFailure: (err) => {
        reject(err);
      },
      newPasswordRequired: (userAttributes, requiredAttributes) => {
        // Handle new password required (for first-time login)
        reject(new Error('New password required. Please check your email for verification.'));
      },
    });
  });
}

/**
 * Get current authenticated user
 * @returns {Promise<Object|null>} Current user or null if not authenticated
 */
export async function getCurrentUser() {
  if (!userPool) {
    return null;
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      resolve(null);
      return;
    }

    cognitoUser.getSession((err, session) => {
      if (err || !session.isValid()) {
        resolve(null);
        return;
      }

      cognitoUser.getUserAttributes((err, attributes) => {
        if (err) {
          reject(err);
          return;
        }

        const userAttributes = {};
        attributes.forEach((attr) => {
          userAttributes[attr.Name] = attr.Value;
        });

        resolve({
          email: userAttributes.email,
          sub: session.getIdToken().payload.sub,
          attributes: userAttributes,
        });
      });
    });
  });
}

/**
 * Sign out the current user
 */
export function signOut() {
  if (!userPool) {
    return;
  }

  const cognitoUser = userPool.getCurrentUser();
  if (cognitoUser) {
    cognitoUser.signOut();
  }
}

/**
 * Refresh the access token using refresh token
 * @param {string} refreshToken - Refresh token
 * @returns {Promise<Object>} New tokens
 */
export async function refreshToken(refreshTokenValue) {
  if (!userPool) {
    throw new Error('Cognito is not configured');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) {
      reject(new Error('No user found'));
      return;
    }

    cognitoUser.refreshSession(
      { getToken: () => refreshTokenValue },
      (err, session) => {
        if (err) {
          reject(err);
          return;
        }

        resolve({
          accessToken: session.getAccessToken().getJwtToken(),
          idToken: session.getIdToken().getJwtToken(),
        });
      }
    );
  });
}

/**
 * Verify email with verification code
 * @param {string} email - User email
 * @param {string} code - Verification code
 * @returns {Promise<void>}
 */
export async function confirmSignUp(email, code) {
  if (!userPool) {
    throw new Error('Cognito is not configured');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.confirmRegistration(code, true, (err, result) => {
      if (err) {
        reject(err);
        return;
      }
      resolve(result);
    });
  });
}

/**
 * Request password reset code
 * @param {string} email - User email
 * @returns {Promise<void>}
 */
export async function forgotPassword(email) {
  if (!userPool) {
    throw new Error('Cognito is not configured');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.forgotPassword({
      onSuccess: (data) => {
        resolve(data);
      },
      onFailure: (err) => {
        reject(err);
      },
    });
  });
}

/**
 * Confirm password reset with code and new password
 * @param {string} email - User email
 * @param {string} code - Verification code
 * @param {string} newPassword - New password
 * @returns {Promise<void>}
 */
export async function confirmPassword(email, code, newPassword) {
  if (!userPool) {
    throw new Error('Cognito is not configured');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.confirmPassword(code, newPassword, {
      onSuccess: () => {
        resolve();
      },
      onFailure: (err) => {
        reject(err);
      },
    });
  });
}

/**
 * Resend confirmation code for signup
 * @param {string} email - User email
 * @returns {Promise<void>}
 */
export async function resendConfirmationCode(email) {
  if (!userPool) {
    throw new Error('Cognito is not configured');
  }

  return new Promise((resolve, reject) => {
    const cognitoUser = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    cognitoUser.resendConfirmationCode((err, result) => {
      if (err) {
        reject(err);
        return;
      }
      resolve(result);
    });
  });
}

