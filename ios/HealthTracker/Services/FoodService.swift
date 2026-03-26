import Foundation

struct FoodService {
    private let api = APIClient.shared

    func items() async throws -> [FoodItem] {
        try await api.request("GET", path: "/api/food/items")
    }

    func addIntake(_ req: AddFoodIntakeRequest) async throws -> MessageResponse {
        try await api.request("POST", path: "/api/food/intake", body: req)
    }

    func deleteIntake(id: Int) async throws {
        try await api.requestVoid("DELETE", path: "/api/food/intake/\(id)")
    }

    func getIntake(days: Int = 30) async throws -> [FoodIntakeRecord] {
        try await api.request("GET", path: "/api/food/intake", query: ["days": "\(days)"])
    }

    func addWater(_ req: AddWaterRequest) async throws -> MessageResponse {
        try await api.request("POST", path: "/api/food/water", body: req)
    }

    func getWater(days: Int = 30) async throws -> [WaterRecord] {
        try await api.request("GET", path: "/api/food/water", query: ["days": "\(days)"])
    }
}
