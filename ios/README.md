# Health Tracker — iOS (SwiftUI)

Native SwiftUI client for the Health Tracker FastAPI backend. Requires **iOS 17+** and **Xcode 15+**.

## Quick start

```bash
# Generate the Xcode project (requires xcodegen — `brew install xcodegen`)
cd ios
xcodegen generate

# Open in Xcode
open HealthTracker.xcodeproj
```

Select the **HealthTracker** scheme, pick a simulator or device, and run.

## Configuration

The API base URL is set per build configuration via xcconfig files:

| File | Default value | Purpose |
|------|--------------|---------|
| `HealthTracker/Config/Debug.xcconfig` | `http://localhost:8000` | Local development |
| `HealthTracker/Config/Release.xcconfig` | `https://api.example.com` | Staging / production |

Edit these before building. The value is injected into `Info.plist` as `API_BASE_URL` and read at runtime by `AppConfig.swift`.

### App Transport Security (ATS)

`Info.plist` includes `NSAllowsLocalNetworking = true` so the debug build can talk to a plain-HTTP server on your LAN. For production, always use HTTPS — the ATS exception only covers local network addresses.

## Architecture

```
HealthTracker/
├── Config/           # xcconfig files + AppConfig
├── Networking/       # APIClient, SSEStreamClient, KeychainHelper
├── Models/           # Codable structs matching API JSON
├── Services/         # Thin wrappers around APIClient per domain
├── Stores/           # AuthStore (@Observable, Keychain-backed)
└── Views/
    ├── Auth/         # LoginView (login + register)
    ├── Workout/      # Dashboard + Log
    ├── Nutrition/    # Dashboard + Log (food + water)
    ├── Progress/     # Progress dashboard (scores, recommendations)
    ├── Body/         # Weight/waist metrics + photo gallery
    ├── Chat/         # AI Trainer (SSE streaming, actions, memories)
    ├── Settings/     # Goals editor
    ├── Admin/        # Exercise catalog CRUD, user data viewer
    └── Components/   # DashboardCard, ScoreGauge, MacroRing
```

## Screens (parity with web frontend)

| Tab | Screens | Web equivalent |
|-----|---------|---------------|
| Workout | Dashboard, Log Workout | `/workout`, `/workout/log` |
| Nutrition | Dashboard, Log Food & Water | `/nutrition`, `/nutrition/log` |
| AI Trainer | Chat (SSE stream + actions) | `/chat` |
| Body | Weight/waist chart, photo gallery | `/body` |
| More | Progress dashboard, Goals & Settings, Admin (if admin), Logout | `/progress`, `/settings`, `/admin/*` |

## Running the backend

The iOS app talks to the same FastAPI server the web app uses. Make sure it is reachable from your device/simulator:

```bash
# From the repo root
docker compose up api mysql
```

If running on a **physical device**, replace `localhost` in `Debug.xcconfig` with your Mac's LAN IP (e.g. `http://192.168.1.42:8000`).

## Testing checklist

- [ ] Login with valid credentials; token is persisted (kill & relaunch).
- [ ] Register a new user; switch to login form; login succeeds.
- [ ] Workout dashboard loads charts; navigate to Log Workout, add exercise + sets, save.
- [ ] Nutrition dashboard loads; log food and water entries.
- [ ] Chat: send a message, see SSE streaming text; confirm/reject action cards.
- [ ] Body: save weight metric, upload photo from library, view in fullscreen, delete via context menu.
- [ ] Settings: load goals, change values, save.
- [ ] Admin (admin account): exercise CRUD (add, edit, toggle active, delete); user data viewer loads per-user tabs.
- [ ] Logout clears session; app shows login screen.
- [ ] 401 from expired token auto-logs out.
