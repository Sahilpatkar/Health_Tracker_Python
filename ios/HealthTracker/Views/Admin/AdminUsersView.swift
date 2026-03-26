import SwiftUI

private let tabs = ["Goals", "Food", "Workouts", "Body", "Water", "Photos", "Chat", "Memory", "Actions"]

struct AdminUsersView: View {
    @State private var users: [AdminUser] = []
    @State private var summary: PlatformSummary?
    @State private var selected: String = ""
    @State private var tab = "Goals"
    @State private var payload: AdminPayload = .none
    @State private var isLoading = false

    private let service = AdminService()

    var body: some View {
        List {
            if let s = summary { summarySection(s) }
            userPickerSection
            tabPickerSection
            dataSection
        }
        .navigationTitle("User Data")
        .task {
            users = (try? await service.listUsers()) ?? []
            summary = try? await service.platformSummary()
        }
        .onChange(of: selected) { _, _ in Task { await loadTab() } }
        .onChange(of: tab) { _, _ in Task { await loadTab() } }
    }

    private func summarySection(_ s: PlatformSummary) -> some View {
        Section("Platform") {
            LabeledContent("Total Users", value: "\(s.totalUsers ?? 0)")
            LabeledContent("Total Workouts", value: "\(s.totalWorkouts ?? 0)")
            LabeledContent("Total Food Logs", value: "\(s.totalFoodLogs ?? 0)")
        }
    }

    private var userPickerSection: some View {
        Section("User") {
            Picker("User", selection: $selected) {
                Text("Choose a user...").tag("")
                ForEach(users) { u in
                    Text("\(u.user) (\(u.role))").tag(u.user)
                }
            }
        }
    }

    private var tabPickerSection: some View {
        Section {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(tabs, id: \.self) { t in
                        Button(t) { tab = t }
                            .font(.caption.bold())
                            .padding(.horizontal, 10).padding(.vertical, 6)
                            .background(tab == t ? Color.indigo : Color(.secondarySystemGroupedBackground),
                                        in: Capsule())
                            .foregroundStyle(tab == t ? .white : .primary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var dataSection: some View {
        Section {
            if selected.isEmpty {
                Text("Select a user to load data.").foregroundStyle(.secondary)
            } else if isLoading {
                ProgressView()
            } else {
                switch payload {
                case .none:
                    Text("No data.").foregroundStyle(.secondary)
                case .text(let text):
                    Text(text).font(.caption.monospaced())
                case .entries(let rows):
                    if rows.isEmpty {
                        Text("No records.").foregroundStyle(.secondary)
                    } else {
                        ForEach(rows.indices, id: \.self) { i in
                            Text(rows[i]).font(.caption.monospaced())
                        }
                    }
                }
            }
        }
    }

    private func loadTab() async {
        guard !selected.isEmpty else { payload = .none; return }
        isLoading = true
        do {
            switch tab {
            case "Goals":
                let g: Goals = try await service.userGoals(username: selected)
                payload = .text("\(g)")
            case "Food":
                let items: [FoodIntakeRecord] = try await service.userFood(username: selected)
                payload = .entries(items.map { "\($0.date)  \($0.mealType)  \($0.foodItem)  ×\($0.quantity)" })
            case "Workouts":
                let sessions: [WorkoutSession] = try await service.userWorkouts(username: selected)
                payload = .entries(sessions.map { "\($0.sessionDate)  \($0.exercises?.count ?? 0) exercises" })
            case "Body":
                let m: [BodyMetric] = try await service.userMetrics(username: selected)
                payload = .entries(m.map { "\($0.date)  \($0.weightKg)kg  waist:\($0.waistCm ?? 0)cm" })
            case "Water":
                let w: [WaterRecord] = try await service.userWater(username: selected)
                payload = .entries(w.map { "\($0.date)  \($0.waterIntake)L" })
            case "Photos":
                let p: [BodyPhoto] = try await service.userPhotos(username: selected)
                payload = .entries(p.map { "\($0.takenDate)  \($0.photoUrl)" })
            case "Chat":
                let msgs: [ChatMessage] = try await service.userChat(username: selected)
                payload = .entries(msgs.map { "[\($0.role)] \($0.content.prefix(120))" })
            case "Memory":
                let mem: [ChatMemory] = try await service.userMemory(username: selected)
                payload = .entries(mem.map { "[\($0.category)] \($0.content)" })
            case "Actions":
                let acts: [PendingAction] = try await service.userPendingActions(username: selected)
                payload = .entries(acts.map { "\($0.actionType)  \($0.createdAt)" })
            default:
                payload = .none
            }
        } catch {
            payload = .text("Error: \(error.localizedDescription)")
        }
        isLoading = false
    }
}

private enum AdminPayload {
    case none
    case text(String)
    case entries([String])
}
