import Foundation

struct FoodItem: Decodable, Identifiable, Hashable {
    let foodId: Int
    let foodItem: String
    let calories: Double?
    let protein: Double?
    let carbs: Double?
    let fat: Double?

    var id: Int { foodId }
}

struct FoodIntakeRecord: Decodable, Identifiable {
    let intakeId: Int
    let foodItem: String
    let quantity: Double
    let unit: String
    let mealType: String
    let date: String
    let calories: Double?
    let protein: Double?
    let carbs: Double?
    let fat: Double?

    var id: Int { intakeId }
}

struct AddFoodIntakeRequest: Encodable {
    let foodId: Int
    let date: String
    let mealType: String
    let foodItem: String
    let quantity: Double
    let unit: String
}

struct WaterRecord: Decodable, Identifiable {
    let waterId: Int?
    let date: String
    let waterIntake: Double

    var id: String { "\(date)-\(waterIntake)" }
}

struct AddWaterRequest: Encodable {
    let date: String
    let waterIntake: Double
}
