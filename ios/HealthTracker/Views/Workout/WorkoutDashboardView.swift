import SwiftUI
import Charts

struct WorkoutDashboardView: View {
    @State private var dashboard: WorkoutDashboard?
    @State private var isLoading = true
    @State private var error: String?

    private let service = MetricsService()

    var body: some View {
        ScrollView {
            if isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity, minHeight: 200)
            } else if let error {
                ContentUnavailableView("Error", systemImage: "exclamationmark.triangle", description: Text(error))
            } else if let dashboard {
                LazyVStack(spacing: 16) {
                    weeklyCountChart(dashboard)
                    volumeTrendChart(dashboard)
                    muscleGroupChart(dashboard)
                }
                .padding()
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Workout")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                NavigationLink(destination: WorkoutLogView()) {
                    Label("Log Workout", systemImage: "plus.circle.fill")
                }
            }
        }
        .task { await load() }
        .refreshable { await load() }
    }

    @ViewBuilder
    private func weeklyCountChart(_ data: WorkoutDashboard) -> some View {
        DashboardCard(title: "Weekly Workout Count") {
            if let weekly = data.weeklyVolume, !weekly.isEmpty {
                Chart(weekly) { entry in
                    BarMark(
                        x: .value("Week", entry.week),
                        y: .value("Volume", entry.volume)
                    )
                    .foregroundStyle(.indigo)
                    .cornerRadius(6)
                }
                .frame(height: 200)
            } else {
                Text("No data yet").foregroundStyle(.secondary).font(.subheadline)
            }
        }
    }

    @ViewBuilder
    private func volumeTrendChart(_ data: WorkoutDashboard) -> some View {
        DashboardCard(title: "Recent Sessions") {
            if let sessions = data.recentSessions, !sessions.isEmpty {
                Chart(sessions) { s in
                    LineMark(
                        x: .value("Date", s.sessionDate),
                        y: .value("Volume", s.totalVolume ?? 0)
                    )
                    .foregroundStyle(.purple)
                    PointMark(
                        x: .value("Date", s.sessionDate),
                        y: .value("Volume", s.totalVolume ?? 0)
                    )
                    .foregroundStyle(.purple)
                }
                .frame(height: 200)
            } else {
                Text("No data yet").foregroundStyle(.secondary).font(.subheadline)
            }
        }
    }

    @ViewBuilder
    private func muscleGroupChart(_ data: WorkoutDashboard) -> some View {
        DashboardCard(title: "Sets by Muscle Group") {
            if let groups = data.muscleGroupBreakdown, !groups.isEmpty {
                Chart(groups) { entry in
                    BarMark(
                        x: .value("Muscle", entry.muscleGroup),
                        y: .value("Sets", entry.sets ?? 0)
                    )
                    .foregroundStyle(.green)
                    .cornerRadius(6)
                }
                .frame(height: 200)
            } else {
                Text("Log workouts to see breakdown").foregroundStyle(.secondary).font(.subheadline)
            }
        }
    }

    private func load() async {
        do {
            dashboard = try await service.workoutDashboard()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}
