import Foundation

struct WorkoutService {
    private let api = APIClient.shared

    func save(_ req: SaveWorkoutRequest) async throws -> MessageResponse {
        try await api.request("POST", path: "/api/workouts", body: req)
    }

    func sessions(days: Int = 60) async throws -> [WorkoutSession] {
        try await api.request("GET", path: "/api/workouts/sessions", query: ["days": "\(days)"])
    }
}
