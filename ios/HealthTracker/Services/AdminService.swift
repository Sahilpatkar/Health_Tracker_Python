import Foundation

struct AdminService {
    private let api = APIClient.shared

    func listUsers() async throws -> [AdminUser] {
        try await api.request("GET", path: "/api/admin/users")
    }

    func userFood(username: String, date: String? = nil) async throws -> [FoodIntakeRecord] {
        var q: [String: String] = [:]
        if let date { q["date"] = date }
        return try await api.request("GET", path: "/api/admin/users/\(username)/food", query: q)
    }

    func userWorkouts(username: String) async throws -> [WorkoutSession] {
        try await api.request("GET", path: "/api/admin/users/\(username)/workouts")
    }

    func userGoals(username: String) async throws -> Goals {
        try await api.request("GET", path: "/api/admin/users/\(username)/goals")
    }

    func userMetrics(username: String) async throws -> [BodyMetric] {
        try await api.request("GET", path: "/api/admin/users/\(username)/metrics")
    }

    func userWater(username: String) async throws -> [WaterRecord] {
        try await api.request("GET", path: "/api/admin/users/\(username)/water")
    }

    func userPhotos(username: String) async throws -> [BodyPhoto] {
        try await api.request("GET", path: "/api/admin/users/\(username)/photos")
    }

    func userChat(username: String) async throws -> [ChatMessage] {
        try await api.request("GET", path: "/api/admin/users/\(username)/chat")
    }

    func userMemory(username: String) async throws -> [ChatMemory] {
        try await api.request("GET", path: "/api/admin/users/\(username)/memory")
    }

    func userPendingActions(username: String) async throws -> [PendingAction] {
        try await api.request("GET", path: "/api/admin/users/\(username)/pending-actions")
    }

    func platformSummary() async throws -> PlatformSummary {
        try await api.request("GET", path: "/api/admin/summary")
    }
}
