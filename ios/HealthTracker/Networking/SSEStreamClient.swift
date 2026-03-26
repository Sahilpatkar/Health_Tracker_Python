import Foundation

enum SSEEvent {
    case text(String)
    case status(String)
    case action(ChatActionData)
    case done(String)
}

/// Streams Server-Sent Events from a POST endpoint using URLSession async bytes.
struct SSEStreamClient {
    private let baseURL: URL
    private let token: String?

    init(baseURL: URL = AppConfig.baseURL, token: String? = nil) {
        self.baseURL = baseURL
        self.token = token
    }

    func stream(
        message: String,
        onEvent: @escaping (SSEEvent) -> Void
    ) async throws {
        let url = baseURL.appendingPathComponent("/api/chat/message")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let body = ["content": message]
        request.httpBody = try JSONEncoder().encode(body)

        let (bytes, response) = try await URLSession.shared.bytes(for: request)

        if let http = response as? HTTPURLResponse, http.statusCode == 401 {
            throw APIError.unauthorized
        }

        var currentEvent = ""
        var currentData = ""

        for try await line in bytes.lines {
            if line.hasPrefix("event: ") {
                currentEvent = String(line.dropFirst(7))
                currentData = ""
            } else if line.hasPrefix("data: ") {
                let chunk = String(line.dropFirst(6))
                currentData += currentData.isEmpty ? chunk : "\n" + chunk
            } else if line.isEmpty, !currentEvent.isEmpty {
                let evt = parseEvent(type: currentEvent, data: currentData)
                if let evt { onEvent(evt) }
                currentEvent = ""
                currentData = ""
            }
        }
    }

    private func parseEvent(type: String, data: String) -> SSEEvent? {
        switch type {
        case "text":
            return .text(data)
        case "status":
            return .status(data)
        case "done":
            return .done(data)
        case "action":
            guard let jsonData = data.data(using: .utf8),
                  let action = try? JSONDecoder.snakeCase.decode(ChatActionData.self, from: jsonData) else {
                return nil
            }
            return .action(action)
        default:
            return .text(data)
        }
    }
}

extension JSONDecoder {
    static let snakeCase: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()
}
