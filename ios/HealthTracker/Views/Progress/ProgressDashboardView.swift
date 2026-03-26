import SwiftUI

struct ProgressDashboardView: View {
    @State private var dashboard: ProgressDashboard?
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
                VStack(spacing: 16) {
                    scoresRow(data)
                    recommendationsSection(data)
                }
                .padding()
            }
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Progress")
        .task { await load() }
        .refreshable { await load() }
    }

    @ViewBuilder
    private func scoresRow(_ data: ProgressDashboard) -> some View {
        DashboardCard {
            HStack(spacing: 24) {
                ScoreGauge(score: data.overallScore ?? 0, label: "Overall", color: .indigo)
                Spacer()
            }
            .frame(maxWidth: .infinity)
        }

        if let recs = data.recommendations, !recs.isEmpty {
            EmptyView() // handled below
        }
    }

    @ViewBuilder
    private func recommendationsSection(_ data: ProgressDashboard) -> some View {
        if let recs = data.recommendations, !recs.isEmpty {
            DashboardCard(title: "Recommendations") {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(recs, id: \.self) { tip in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "lightbulb.fill")
                                .foregroundStyle(.yellow)
                                .font(.caption)
                            Text(tip)
                                .font(.subheadline)
                        }
                    }
                }
            }
        }
    }

    private func load() async {
        do {
            dashboard = try await service.progressDashboard()
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}
