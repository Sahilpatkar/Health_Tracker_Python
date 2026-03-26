import Foundation

struct WorkoutDashboard: Decodable {
    let recentSessions: [DashboardSession]?
    let weeklyVolume: [WeeklyVolume]?
    let muscleGroupBreakdown: [MuscleGroupEntry]?
    let currentStreak: Int?
    let totalSessions: Int?
}

struct DashboardSession: Decodable, Identifiable {
    let sessionId: Int
    let sessionDate: String
    let exerciseCount: Int?
    let totalSets: Int?
    let totalVolume: Double?

    var id: Int { sessionId }
}

struct WeeklyVolume: Decodable, Identifiable {
    let week: String
    let volume: Double

    var id: String { week }
}

struct MuscleGroupEntry: Decodable, Identifiable {
    let muscleGroup: String
    let sets: Int?
    let volume: Double?

    var id: String { muscleGroup }
}

struct NutritionDashboard: Decodable {
    let todaySummary: DaySummary?
    let weeklyAverage: DaySummary?
    let recentDays: [DayEntry]?
    let goals: Goals?
}

struct DaySummary: Decodable {
    let calories: Double?
    let protein: Double?
    let carbs: Double?
    let fat: Double?
    let water: Double?
}

struct DayEntry: Decodable, Identifiable {
    let date: String
    let calories: Double?
    let protein: Double?
    let carbs: Double?
    let fat: Double?

    var id: String { date }
}

struct ProgressDashboard: Decodable {
    let bodyMetrics: [BodyMetric]?
    let workoutProgress: [WorkoutProgressEntry]?
    let nutritionTrend: [DayEntry]?
    let overallScore: Double?
    let recommendations: [String]?
}

struct WorkoutProgressEntry: Decodable, Identifiable {
    let exerciseName: String?
    let date: String?
    let maxWeight: Double?
    let totalVolume: Double?

    var id: String { "\(exerciseName ?? "")-\(date ?? "")" }
}
