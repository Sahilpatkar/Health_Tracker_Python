import Foundation

struct Exercise: Codable, Identifiable, Hashable {
    let exerciseId: Int
    let name: String
    let muscleGroup: String
    let equipment: String
    let isActive: Bool?

    var id: Int { exerciseId }
}

struct CreateExerciseRequest: Encodable {
    let name: String
    let muscleGroup: String
    let equipment: String
}

struct UpdateExerciseRequest: Encodable {
    let name: String?
    let muscleGroup: String?
    let equipment: String?
    let isActive: Bool?
}
