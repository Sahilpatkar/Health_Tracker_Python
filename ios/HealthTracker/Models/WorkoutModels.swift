import Foundation

struct WorkoutSet: Codable {
    let reps: Int
    let weight: Double
    let rpe: Double?
    let rir: Double?
}

struct WorkoutExerciseEntry: Codable {
    let exerciseId: Int
    let sets: [WorkoutSet]
}

struct SaveWorkoutRequest: Encodable {
    let sessionDate: String
    let notes: String?
    let exercises: [WorkoutExerciseEntry]
}

struct WorkoutSession: Decodable, Identifiable {
    let sessionId: Int
    let sessionDate: String
    let notes: String?
    let exercises: [SessionExercise]?

    var id: Int { sessionId }
}

struct SessionExercise: Decodable, Identifiable {
    let exerciseName: String
    let muscleGroup: String
    let sets: [WorkoutSet]

    var id: String { exerciseName }
}
