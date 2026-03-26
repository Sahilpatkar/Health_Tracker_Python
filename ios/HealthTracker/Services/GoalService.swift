import Foundation

struct GoalService {
    private let api = APIClient.shared

    func get() async throws -> Goals {
        try await api.request("GET", path: "/api/goals")
    }

    func update(_ goals: Goals) async throws -> MessageResponse {
        try await api.request("PUT", path: "/api/goals", body: goals)
    }
}
