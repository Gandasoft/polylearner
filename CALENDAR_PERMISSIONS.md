# Calendar Permissions Guide

## Problem
Users are seeing "Calendar permission denied" errors when tasks are being auto-scheduled to Google Calendar.

## Root Cause
The user's Google OAuth token doesn't include the required calendar scopes. This happens when:
1. The user signed in before calendar integration was added
2. The user denied calendar permissions during OAuth flow
3. The OAuth app configuration doesn't request calendar scopes

## Solution for Users

### Re-Authenticate with Calendar Permissions

**Step 1: Sign Out**
- Click your profile/settings
- Select "Sign Out"

**Step 2: Remove Previous Authorization (if needed)**
- Visit: https://myaccount.google.com/permissions
- Find "PolyLearner" in the list
- Click "Remove Access"

**Step 3: Sign In Again**
- Go back to the PolyLearner app
- Click "Sign In with Google"
- **Important**: When Google shows the permissions screen, make sure to:
  - ✅ Allow access to your Google Calendar
  - ✅ Allow access to create and manage calendar events
  - ✅ Grant all requested permissions

**Step 4: Verify**
- Create a new task
- You should see a success message: "Task successfully scheduled on your calendar"
- Check your Google Calendar to see the event

## Solution for Developers

### Required OAuth Scopes

Make sure your Google OAuth app includes these scopes:
```
https://www.googleapis.com/auth/userinfo.profile
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/calendar
https://www.googleapis.com/auth/calendar.events
```

### Frontend Changes Made

1. **NewTaskDialog.tsx**: Added toast notifications
   - Shows success message when task is scheduled
   - Shows error message when calendar permission is denied
   - Provides clear instructions to re-authenticate

2. **GoalOnboarding.tsx**: Added calendar error handling
   - Checks all created tasks for calendar errors
   - Shows consolidated error message if any task fails
   - Guides user to re-authenticate

3. **api.ts**: Updated Task interface
   - Added `calendar_scheduling` field to Task type
   - Includes both success (scheduled events) and error information

### Backend Already Handles This

The backend (app.py) already:
- Detects 403 Forbidden errors from Google Calendar API
- Returns structured error with `error_code: "calendar_permission_denied"`
- Includes helpful error message in response
- Logs errors for debugging

## User-Facing Error Messages

### When Creating Individual Tasks
```
🔴 Calendar Access Required
Please sign out and sign back in, granting calendar permissions to enable auto-scheduling.
```

### When Creating Tasks During Onboarding
```
🔴 Tasks Created (Calendar Access Required)
Your tasks were created but couldn't be scheduled. Please sign out and sign back in, 
granting calendar permissions to enable auto-scheduling.
```

### When Task Successfully Scheduled
```
✅ Task Scheduled
Task successfully scheduled on your calendar for [date/time].
```

## Testing

1. **Test without calendar permissions**:
   - Create a fresh Google account
   - Sign in to PolyLearner but deny calendar permissions
   - Try creating a task → Should see error message
   - Sign out and back in, grant permissions
   - Try again → Should see success message

2. **Test with existing calendar events**:
   - Add some events to your Google Calendar
   - Create a task in PolyLearner
   - Verify it doesn't conflict with existing events

3. **Test onboarding flow**:
   - Complete the goal onboarding
   - Create multiple tasks
   - Verify they're all scheduled to calendar
   - Or see consolidated error if permissions denied

## Monitoring

Check backend logs for:
```
WARNING - Calendar permission denied for user {user_id}
```

This indicates users need to re-authenticate.

## Future Improvements

1. **Token Refresh**: Implement automatic token refresh for expired tokens
2. **Proactive Check**: Check calendar permissions on login and show warning if missing
3. **Settings Page**: Add calendar connection status indicator
4. **Re-auth Button**: Add one-click re-authentication from settings
5. **Graceful Degradation**: Allow users to continue without calendar integration
