import { useState } from 'react';
import { validateField, validateForm } from '../utils/validation';

/**
 * React hook for form validation
 */
export function useFormValidation(initialValues, schema) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleChange = (field, value) => {
    setValues((prev) => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleBlur = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    
    // Validate on blur - pass all values for cross-field validation
    if (schema[field]) {
      const error = validateField(values[field], schema[field], values);
      if (error) {
        setErrors((prev) => ({ ...prev, [field]: error }));
      } else {
        // Clear error if validation passes
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors[field];
          return newErrors;
        });
      }
    }
  };

  const validate = () => {
    const result = validateForm(values, schema);
    setErrors(result.errors);
    setTouched(
      Object.keys(schema).reduce((acc, key) => ({ ...acc, [key]: true }), {})
    );
    return result.isValid;
  };

  const reset = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  };

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validate,
    reset,
    setValues,
  };
}

