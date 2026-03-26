import SwiftUI
import Charts

struct NutritionDashboardView: View {
    @State private var dashboard: NutritionDashboard?
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
            } else if let data = dashboard {
                LazyVStack(spacing: 16) {
                    todaySection(data)
                    adherenceSection(data)
                    recentDaysChart(data)
                }
                .padding()
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Nutrition")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                NavigationLink(destination: NutritionLogView()) {
                    Label("Log Food", systemImage: "plus.circle.fill")
                }
            }
        }
        .task { await load() }
        .refreshable { await load() }
    }

    @ViewBuilder
    private func todaySection(_ data: NutritionDashboard) -> some View {
        if let today = data.todaySummary, let goals = data.goals {
            DashboardCard(title: "Today's Intake") {
                HStack(spacing: 24) {
                    MacroRing(
                        value: today.calories ?? 0,
                        target: goals.calorieTarget,
                        label: "Calories",
                        color: .indigo
                    )
                    MacroRing(
                        value: today.protein ?? 0,
                        target: goals.proteinTarget,
                        label: "Protein (g)",
                        color: .green
                    )
                    MacroRing(
                        value: today.carbs ?? 0,
                        target: goals.carbTarget,
                        label: "Carbs (g)",
                        color: .orange
                    )
                }
                .frame(maxWidth: .infinity)
            }
        }
    }

    @ViewBuilder
    private func adherenceSection(_ data: NutritionDashboard) -> some View {
        if let avg = data.weeklyAverage, let goals = data.goals {
            DashboardCard(title: "7-Day Averages") {
                VStack(spacing: 10) {
                    adherenceRow(label: "Calories", value: avg.calories ?? 0, target: goals.calorieTarget, color: .indigo)
                    adherenceRow(label: "Protein", value: avg.protein ?? 0, target: goals.proteinTarget, color: .green)
                }
            }
        }
    }

    private func adherenceRow(label: String, value: Double, target: Double, color: Color) -> some View {
        let pct = target > 0 ? min(value / target, 1.0) : 0
        return VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label).font(.subheadline)
                Spacer()
                Text("\(Int(pct * 100))%").font(.subheadline.bold())
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color.opacity(0.2))
                    RoundedRectangle(cornerRadius: 4)
                        .fill(color)
                        .frame(width: geo.size.width * pct)
                }
            }
            .frame(height: 8)
        }
    }

    @ViewBuilder
    private func recentDaysChart(_ data: NutritionDashboard) -> some View {
        if let days = data.recentDays, !days.isEmpty {
            DashboardCard(title: "Daily Calories") {
                Chart(days) { d in
                    BarMark(
                        x: .value("Date", d.date),
                        y: .value("Calories", d.calories ?? 0)
                    )
                    .foregroundStyle(.indigo)
                    .cornerRadius(4)
                }
                .frame(height: 200)
            }
        }
    }

    private func load() async {
        do {
            dashboard = try await service.nutritionDashboard()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}
