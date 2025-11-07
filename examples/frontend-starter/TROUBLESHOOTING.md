# Troubleshooting Guide

## Login Issues

### Page Refreshes and Returns to Login

**Problem**: After clicking login, the page refreshes and stays on the login page.

**Solution**: This was a timing issue with React state updates. The fix includes:
1. Checking localStorage in ProtectedRoute as a fallback
2. Using `replace: true` in navigation to prevent back button issues
3. Small delay to ensure state updates propagate

**If issue persists**:
- Clear browser localStorage: `localStorage.clear()`
- Check browser console for errors
- Verify the AuthContext is properly wrapping the app

### Authentication State Not Persisting

**Problem**: User gets logged out on page refresh.

**Solution**: The app checks localStorage on mount. Ensure:
- `auth_token` is stored in localStorage after login
- Browser allows localStorage (not in private/incognito mode)
- No browser extensions blocking localStorage

---

## API Connection Issues

### API Calls Failing

**Problem**: Frontend can't connect to backend API.

**Solutions**:
1. Check API is running: `http://localhost:8000/health`
2. Verify `VITE_API_BASE_URL` in `.env.local`
3. Check CORS settings in backend
4. Verify network tab in browser DevTools

### CORS Errors

**Problem**: Browser shows CORS errors in console.

**Solution**: 
- Backend needs to allow frontend origin
- Check `src/api/main.py` for CORS middleware configuration
- Ensure frontend URL is in allowed origins

---

## Build Issues

### npm install Fails

**Problem**: npm install shows errors.

**Solutions**:
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then reinstall
- Check Node.js version (should be 18+)

### Vite Build Errors

**Problem**: `npm run dev` fails.

**Solutions**:
- Check Node.js version
- Clear `.vite` cache directory
- Reinstall dependencies

---

## Common Fixes

### Clear All Data
```javascript
// In browser console
localStorage.clear();
sessionStorage.clear();
```

### Reset Environment
```bash
# Delete and recreate
rm -rf node_modules package-lock.json
npm install
```

### Check Backend
```bash
# Verify API is running
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

---

## Still Having Issues?

1. Check browser console for errors
2. Check network tab for failed requests
3. Verify backend is running and accessible
4. Check environment variables are set correctly
5. Review `README.md` for setup instructions

