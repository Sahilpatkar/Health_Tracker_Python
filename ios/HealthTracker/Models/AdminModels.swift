import Foundation

struct AdminUser: Decodable, Identifiable {
    let userId: Int
    let user: String
    let role: String

    var id: Int { userId }
}

struct PlatformSummary: Decodable {
    let totalUsers: Int?
    let totalWorkouts: Int?
    let totalFoodLogs: Int?
    let activeToday: Int?
}

struct PendingAction: Decodable, Identifiable {
    let actionId: Int
    let actionType: String
    let createdAt: String

    var id: Int { actionId }
}
