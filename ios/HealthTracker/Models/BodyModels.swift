import Foundation

struct BodyMetric: Decodable, Identifiable {
    let metricId: Int?
    let date: String
    let weightKg: Double
    let waistCm: Double?

    var id: String { "\(date)-\(weightKg)" }
}

struct SaveBodyMetricsRequest: Encodable {
    let date: String
    let weightKg: Double
    let waistCm: Double?
}

struct BodyPhoto: Decodable, Identifiable, Hashable {
    let photoId: Int
    let takenDate: String
    let photoUrl: String
    let notes: String?

    var id: Int { photoId }
}

struct PhotoUploadResponse: Decodable {
    let message: String
    let path: String?
}
