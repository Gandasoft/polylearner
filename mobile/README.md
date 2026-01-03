# PolyLearner Mobile

Flutter mobile client for the PolyLearner productivity app.

## Features

### 📱 Three Main Screens

1. **Dashboard Screen**
   - Current focus task with timer
   - AI-powered insights and suggestions
   - Productivity and cognitive load metrics
   - Upcoming tasks list
   - Interactive charts and statistics

2. **New Task Screen**
   - Quick task creation interface
   - AI suggestions based on context
   - Project and duration selection
   - Priority and urgency flags
   - Rich task details with notes

3. **Calendar View**
   - Weekly/monthly calendar views
   - Time-based event scheduling
   - Focus session tracking
   - Task batching suggestions
   - AI-powered scheduling recommendations

## Getting Started

### Prerequisites

- Flutter SDK (>=3.0.0)
- Dart SDK
- Android Studio / Xcode (for mobile development)

### Installation

1. Navigate to the mobile directory:
```bash
cd mobile
```

2. Install dependencies:
```bash
flutter pub get
```

3. Run the app:
```bash
flutter run
```

## Project Structure

```
mobile/
├── lib/
│   ├── main.dart              # App entry point and navigation
│   ├── theme/
│   │   └── app_theme.dart     # Dark theme configuration
│   └── screens/
│       ├── dashboard_screen.dart
│       ├── new_task_screen.dart
│       └── calendar_screen.dart
└── pubspec.yaml               # Dependencies
```

## Dependencies

- **flutter**: UI framework
- **table_calendar**: Calendar widget
- **fl_chart**: Charts and graphs
- **intl**: Date formatting
- **flutter_svg**: SVG support

## Design System

### Colors
- Primary Blue: `#4C6FFF`
- Dark Background: `#0F1419`
- Card Background: `#1A1D2E`
- Success: `#00D9A3`
- Warning: `#FFB800`
- Error: `#FF4757`

### Typography
- Headlines: Bold, 24-32px
- Body: Regular, 14-16px
- Captions: 11-12px with letter spacing

## Development

### Adding New Screens

1. Create screen file in `lib/screens/`
2. Import in `main.dart`
3. Add navigation route
4. Update bottom navigation if needed

### Customizing Theme

Edit `lib/theme/app_theme.dart` to modify colors, typography, and component styles.

## Building for Production

### Android
```bash
flutter build apk --release
```

### iOS
```bash
flutter build ios --release
```

## Contributing

1. Create feature branch
2. Make changes
3. Test on both iOS and Android
4. Submit pull request

## License

Copyright © 2024 PolyLearner
