import Foundation
import Observation

@Observable
final class AuthStore {
    private(set) var token: String?
    private(set) var username: String?
    private(set) var role: String?

    var isLoggedIn: Bool { token != nil }
    var isAdmin: Bool { role == "admin" }

    private enum Keys {
        static let token = "jwt_token"
        static let username = "username"
        static let role = "role"
    }

    init() {
        self.token = KeychainHelper.loadString(key: Keys.token)
        self.username = KeychainHelper.loadString(key: Keys.username)
        self.role = KeychainHelper.loadString(key: Keys.role)
    }

    func login(token: String, username: String, role: String) {
        self.token = token
        self.username = username
        self.role = role
        KeychainHelper.saveString(token, for: Keys.token)
        KeychainHelper.saveString(username, for: Keys.username)
        KeychainHelper.saveString(role, for: Keys.role)
    }

    func logout() {
        token = nil
        username = nil
        role = nil
        KeychainHelper.delete(key: Keys.token)
        KeychainHelper.delete(key: Keys.username)
        KeychainHelper.delete(key: Keys.role)
    }
}
