# AI Study Companion - Frontend Application

Complete React frontend application for the AI Study Companion platform.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. Start Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

---

## 📄 Pages

### 1. Login
- Email/password authentication
- Mock auth (ready for AWS Cognito)
- Success notifications

### 2. Dashboard
- Progress overview
- Gamification summary
- Quick actions

### 3. Practice
- Subject selection
- Practice assignments
- Answer submission

### 4. Q&A
- Conversational interface
- Confidence display
- Follow-up detection

### 5. Progress
- Goals display
- Session history
- Practice statistics

### 6. Goals
- Goal management
- Create/edit goals
- Progress tracking

### 7. Settings
- Profile information
- Notification preferences
- Account management

### 8. Messaging
- Thread list
- Message view
- Send messages

### 9. Gamification
- Level & XP display
- Badges collection
- Leaderboard

---

## 🧩 Components

### Navigation
- **Navbar** - Complete navigation with all links

### UI Components
- **LoadingSpinner** - Reusable loading component
- **Toast** - Notification component
- **ToastContainer** - Toast management

### Contexts
- **AuthContext** - Authentication state
- **ToastContext** - Notification system

---

## 🎨 Styling

### Theme System
- CSS variables for theming
- Consistent design
- Responsive layout

### Pages
- All pages fully styled
- Mobile responsive
- Consistent UX

---

## 🔌 API Integration

### API Client
- Complete API client in `src/services/apiClient.js`
- All 64 endpoints integrated
- Error handling
- Development mode support

### Endpoints Used
- Summaries
- Practice
- Q&A
- Progress
- Gamification
- Goals
- Messaging
- And more...

---

## 🛠️ Development

### Available Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

### Project Structure
```
src/
├── components/    # Reusable components
├── pages/         # Page components
├── contexts/      # React contexts
├── services/      # API client
├── styles/        # Global styles
└── App.jsx        # Main app
```

---

## 🔐 Authentication

### Current Implementation
- Mock authentication (localStorage)
- Ready for AWS Cognito integration
- Token management
- Protected routes

### To Integrate Cognito
1. Install AWS Amplify
2. Configure Cognito
3. Replace mock auth in `AuthContext.jsx`

---

## 📱 Features

### Implemented
- ✅ Authentication flow
- ✅ Protected routes
- ✅ Toast notifications
- ✅ Loading states
- ✅ Error handling
- ✅ API integration
- ✅ Responsive design

### Ready for Enhancement
- 🔄 Form validation
- 🔄 Real-time updates
- 🔄 Accessibility
- 🔄 Performance optimization

---

## 🐛 Troubleshooting

### API Calls Failing
- Check backend is running: `http://localhost:8000/health`
- Verify `VITE_API_BASE_URL` in `.env.local`
- Check browser console for errors

### Login Issues
- Clear localStorage: `localStorage.clear()`
- Check browser console
- See `TROUBLESHOOTING.md` for details

### Build Issues
- Clear cache: `rm -rf node_modules .vite`
- Reinstall: `npm install`
- Check Node.js version (18+)

---

## 📚 Documentation

- `FEATURES_COMPLETE.md` - Complete feature list
- `FRONTEND_COMPLETE.md` - Implementation status
- `NEXT_STEPS.md` - Development roadmap
- `TROUBLESHOOTING.md` - Common issues

---

## 🎯 Next Steps

1. **Start Backend** - Connect to real API
2. **Test Integration** - Verify all endpoints
3. **Add Validation** - Form validation
4. **Deploy** - Production deployment

---

**The frontend is complete and ready for backend integration!**
