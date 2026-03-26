import SwiftUI

struct ContentView: View {
    @Environment(AuthStore.self) private var auth

    var body: some View {
        if auth.isLoggedIn {
            MainTabView()
        } else {
            LoginView()
        }
    }
}

struct MainTabView: View {
    @Environment(AuthStore.self) private var auth

    var body: some View {
        TabView {
            NavigationStack {
                WorkoutDashboardView()
            }
            .tabItem { Label("Workout", systemImage: "dumbbell") }

            NavigationStack {
                NutritionDashboardView()
            }
            .tabItem { Label("Nutrition", systemImage: "fork.knife") }

            NavigationStack {
                ChatView()
            }
            .tabItem { Label("AI Trainer", systemImage: "bubble.left.and.text.bubble.right") }

            NavigationStack {
                BodyProgressView()
            }
            .tabItem { Label("Body", systemImage: "figure.arms.open") }

            NavigationStack {
                MoreMenuView()
            }
            .tabItem { Label("More", systemImage: "ellipsis.circle") }
        }
    }
}

struct MoreMenuView: View {
    @Environment(AuthStore.self) private var auth

    var body: some View {
        List {
            NavigationLink(destination: ProgressDashboardView()) {
                Label("Progress Dashboard", systemImage: "chart.line.uptrend.xyaxis")
            }
            NavigationLink(destination: SettingsView()) {
                Label("Goals & Settings", systemImage: "gearshape")
            }
            if auth.isAdmin {
                Section("Admin") {
                    NavigationLink(destination: AdminExercisesView()) {
                        Label("Exercise Catalog", systemImage: "list.bullet.clipboard")
                    }
                    NavigationLink(destination: AdminUsersView()) {
                        Label("User Data", systemImage: "person.2")
                    }
                }
            }
            Section {
                Button(role: .destructive) {
                    auth.logout()
                } label: {
                    Label("Logout", systemImage: "rectangle.portrait.and.arrow.right")
                }
            }
        }
        .navigationTitle("More")
    }
}
