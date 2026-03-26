import Foundation

struct Goals: Codable {
    var goalType: String
    var calorieTarget: Double
    var proteinTarget: Double
    var carbTarget: Double
    var fatTarget: Double
    var trainingDaysPerWeek: Int
}
