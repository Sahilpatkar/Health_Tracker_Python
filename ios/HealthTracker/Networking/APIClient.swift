import Foundation

enum APIError: LocalizedError {
    case unauthorized
    case conflict(String)
    case server(Int, String)
    case network(Error)
    case decodingFailed(Error)

    var errorDescription: String? {
        switch self {
        case .unauthorized: return "Session expired. Please log in again."
        case .conflict(let msg): return msg
        case .server(let code, let msg): return "Server error \(code): \(msg)"
        case .network(let err): return err.localizedDescription
        case .decodingFailed(let err): return "Decoding error: \(err.localizedDescription)"
        }
    }
}

@MainActor
final class APIClient {
    static let shared = APIClient()

    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        return URLSession(configuration: config)
    }()

    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    private let encoder: JSONEncoder = {
        let e = JSONEncoder()
        e.keyEncodingStrategy = .convertToSnakeCase
        return e
    }()

    var authStore: AuthStore?

    private var baseURL: URL { AppConfig.baseURL }

    // MARK: - Generic request

    func request<T: Decodable>(
        _ method: String,
        path: String,
        body: (any Encodable)? = nil,
        query: [String: String] = [:]
    ) async throws -> T {
        let data = try await rawRequest(method, path: path, body: body, query: query)
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingFailed(error)
        }
    }

    @discardableResult
    func requestVoid(
        _ method: String,
        path: String,
        body: (any Encodable)? = nil,
        query: [String: String] = [:]
    ) async throws -> Data {
        try await rawRequest(method, path: path, body: body, query: query)
    }

    // MARK: - Multipart upload

    func upload<T: Decodable>(
        path: String,
        fields: [String: String],
        fileField: String,
        fileName: String,
        mimeType: String,
        fileData: Data
    ) async throws -> T {
        let boundary = UUID().uuidString
        var request = try buildRequest("POST", path: path)
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        for (key, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(fileField)\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(fileData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (data, response) = try await perform(request)
        try checkStatus(response, data: data)
        return try decoder.decode(T.self, from: data)
    }

    // MARK: - Internals

    @discardableResult
    private func rawRequest(
        _ method: String,
        path: String,
        body: (any Encodable)? = nil,
        query: [String: String] = [:]
    ) async throws -> Data {
        var request = try buildRequest(method, path: path, query: query)
        if let body {
            request.httpBody = try encoder.encode(body)
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        let (data, response) = try await perform(request)
        try checkStatus(response, data: data)
        return data
    }

    private func buildRequest(
        _ method: String,
        path: String,
        query: [String: String] = [:]
    ) throws -> URLRequest {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        guard let url = components.url else { throw URLError(.badURL) }
        var req = URLRequest(url: url)
        req.httpMethod = method
        if let token = authStore?.token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return req
    }

    private func perform(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw URLError(.badServerResponse)
            }
            return (data, http)
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.network(error)
        }
    }

    private func checkStatus(_ response: HTTPURLResponse, data: Data) throws {
        switch response.statusCode {
        case 200..<300:
            return
        case 401:
            authStore?.logout()
            throw APIError.unauthorized
        case 409:
            let msg = (try? decoder.decode(ErrorDetail.self, from: data))?.detail ?? "Conflict"
            throw APIError.conflict(msg)
        default:
            let msg = (try? decoder.decode(ErrorDetail.self, from: data))?.detail ?? "Unknown error"
            throw APIError.server(response.statusCode, msg)
        }
    }
}

private struct ErrorDetail: Decodable {
    let detail: String
}
