import Foundation

struct AuthService {
    private let api = APIClient.shared

    func login(username: String, password: String) async throws -> LoginResponse {
        try await api.request("POST", path: "/api/auth/login", body: LoginRequest(username: username, password: password))
    }

    func register(username: String, password: String) async throws -> RegisterResponse {
        try await api.request("POST", path: "/api/auth/register", body: RegisterRequest(username: username, password: password))
    }

    func me() async throws -> MeResponse {
        try await api.request("GET", path: "/api/auth/me")
    }
}
