import Foundation

struct LoginRequest: Encodable {
    let username: String
    let password: String
}

struct RegisterRequest: Encodable {
    let username: String
    let password: String
}

struct LoginResponse: Decodable {
    let token: String
    let username: String
    let role: String
}

struct RegisterResponse: Decodable {
    let message: String
}

struct MeResponse: Decodable {
    let username: String
    let role: String
}
