import Foundation

struct MetricsService {
    private let api = APIClient.shared

    func workoutDashboard() async throws -> WorkoutDashboard {
        try await api.request("GET", path: "/api/metrics/workout-dashboard")
    }

    func nutritionDashboard() async throws -> NutritionDashboard {
        try await api.request("GET", path: "/api/metrics/nutrition-dashboard")
    }

    func progressDashboard() async throws -> ProgressDashboard {
        try await api.request("GET", path: "/api/metrics/progress-dashboard")
    }
}
