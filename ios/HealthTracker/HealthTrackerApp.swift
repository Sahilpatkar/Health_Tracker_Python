import SwiftUI

@main
struct HealthTrackerApp: App {
    @State private var authStore = AuthStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(authStore)
                .onAppear {
                    APIClient.shared.authStore = authStore
                }
        }
    }
}
