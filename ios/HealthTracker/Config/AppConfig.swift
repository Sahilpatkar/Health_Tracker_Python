import Foundation

enum AppConfig {
    static let apiBaseURL: String = {
        guard let raw = Bundle.main.infoDictionary?["API_BASE_URL"] as? String,
              !raw.isEmpty else {
            return "http://localhost:8000"
        }
        return raw
    }()

    static var baseURL: URL {
        URL(string: apiBaseURL)!
    }

    /// Media base URL strips a trailing `/api` if present so `/uploads/...` paths resolve correctly.
    static var mediaBaseURL: URL {
        let str = apiBaseURL.hasSuffix("/api")
            ? String(apiBaseURL.dropLast(4))
            : apiBaseURL
        return URL(string: str)!
    }
}
