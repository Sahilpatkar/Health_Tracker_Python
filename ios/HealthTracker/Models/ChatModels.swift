import Foundation

struct ChatMessage: Decodable, Identifiable {
    let id: Int
    let role: String
    let content: String
    let createdAt: String
    let actionData: [ChatActionData]?
}

struct ChatActionData: Decodable, Identifiable {
    let actionId: Int
    let actionType: String
    let displayData: [String: AnyCodable]?

    var id: Int { actionId }
}

struct ChatMemory: Decodable, Identifiable {
    let id: Int
    let category: String
    let content: String
    let createdAt: String
}

struct ActionResponse: Decodable {
    let actionType: String?
    let message: String?
    let error: String?
}

struct MessageResponse: Decodable {
    let message: String
}

/// Type-erased Codable wrapper for dynamic JSON values in action display data.
struct AnyCodable: Decodable, @unchecked Sendable {
    let value: Any

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let v = try? container.decode(String.self) { value = v }
        else if let v = try? container.decode(Double.self) { value = v }
        else if let v = try? container.decode(Bool.self) { value = v }
        else if let v = try? container.decode(Int.self) { value = v }
        else if let v = try? container.decode([String: AnyCodable].self) { value = v }
        else if let v = try? container.decode([AnyCodable].self) { value = v }
        else { value = NSNull() }
    }
}
