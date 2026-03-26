import Foundation

struct BodyService {
    private let api = APIClient.shared

    func saveMetrics(_ req: SaveBodyMetricsRequest) async throws -> MessageResponse {
        try await api.request("POST", path: "/api/body/metrics", body: req)
    }

    func getMetrics() async throws -> [BodyMetric] {
        try await api.request("GET", path: "/api/body/metrics")
    }

    func uploadPhoto(imageData: Data, takenDate: String, notes: String?) async throws -> PhotoUploadResponse {
        var fields = ["taken_date": takenDate]
        if let notes { fields["notes"] = notes }
        return try await api.upload(
            path: "/api/body/photos",
            fields: fields,
            fileField: "file",
            fileName: "photo.jpg",
            mimeType: "image/jpeg",
            fileData: imageData
        )
    }

    func getPhotos() async throws -> [BodyPhoto] {
        try await api.request("GET", path: "/api/body/photos")
    }

    func deletePhoto(id: Int) async throws {
        try await api.requestVoid("DELETE", path: "/api/body/photos/\(id)")
    }
}
