import Foundation

struct ExerciseService {
    private let api = APIClient.shared

    func getActive(muscleGroup: String? = nil) async throws -> [Exercise] {
        var query: [String: String] = [:]
        if let mg = muscleGroup { query["muscle_group"] = mg }
        return try await api.request("GET", path: "/api/exercises", query: query)
    }

    func getAll() async throws -> [Exercise] {
        try await api.request("GET", path: "/api/exercises/all")
    }

    func create(_ req: CreateExerciseRequest) async throws -> Exercise {
        try await api.request("POST", path: "/api/exercises", body: req)
    }

    func update(id: Int, _ req: UpdateExerciseRequest) async throws -> Exercise {
        try await api.request("PUT", path: "/api/exercises/\(id)", body: req)
    }

    func delete(id: Int) async throws {
        try await api.requestVoid("DELETE", path: "/api/exercises/\(id)")
    }
}
