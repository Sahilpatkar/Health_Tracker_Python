import Foundation

struct ChatService {
    private let api = APIClient.shared

    func history(limit: Int = 50) async throws -> [ChatMessage] {
        try await api.request("GET", path: "/api/chat/history", query: ["limit": "\(limit)"])
    }

    func clearHistory() async throws {
        try await api.requestVoid("DELETE", path: "/api/chat/history")
    }

    func confirmAction(actionId: Int) async throws -> ActionResponse {
        struct Body: Encodable { let actionId: Int }
        return try await api.request("POST", path: "/api/chat/confirm-action", body: Body(actionId: actionId))
    }

    func rejectAction(actionId: Int) async throws -> ActionResponse {
        struct Body: Encodable { let actionId: Int }
        return try await api.request("POST", path: "/api/chat/reject-action", body: Body(actionId: actionId))
    }

    func getMemories() async throws -> [ChatMemory] {
        try await api.request("GET", path: "/api/chat/memories")
    }

    func deleteMemory(id: Int) async throws {
        try await api.requestVoid("DELETE", path: "/api/chat/memories/\(id)")
    }
}
