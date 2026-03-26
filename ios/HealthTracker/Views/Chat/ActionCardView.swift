import SwiftUI

struct ActionCardView: View {
    let action: ChatActionData
    let onResolved: () async -> Void

    @State private var resolved = false
    @State private var resolvedStatus: String?
    private let service = ChatService()

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(action.actionType.replacingOccurrences(of: "_", with: " ").capitalized,
                  systemImage: iconName)
                .font(.subheadline.bold())
            if let data = action.displayData {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(Array(data.keys.sorted()), id: \.self) { key in
                        HStack(alignment: .top) {
                            Text(key.replacingOccurrences(of: "_", with: " ") + ":")
                                .font(.caption.bold())
                                .foregroundStyle(.secondary)
                            Text(String(describing: data[key]?.value ?? ""))
                                .font(.caption)
                        }
                    }
                }
            }
            if resolved {
                Text(resolvedStatus ?? "Done")
                    .font(.caption.bold())
                    .foregroundStyle(.green)
            } else {
                HStack(spacing: 12) {
                    Button {
                        Task { await confirm() }
                    } label: {
                        Label("Confirm", systemImage: "checkmark")
                            .font(.caption.bold())
                    }
                    .buttonStyle(.borderedProminent).tint(.green)
                    .clipShape(.rect(cornerRadius: 8))

                    Button(role: .destructive) {
                        Task { await reject() }
                    } label: {
                        Label("Reject", systemImage: "xmark")
                            .font(.caption.bold())
                    }
                    .buttonStyle(.bordered)
                    .clipShape(.rect(cornerRadius: 8))
                }
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 12))
    }

    private var iconName: String {
        switch action.actionType {
        case "update_goals": return "target"
        case "create_workout": return "dumbbell"
        case "log_food": return "fork.knife"
        case "log_water": return "drop"
        default: return "bolt"
        }
    }

    private func confirm() async {
        do {
            let res = try await service.confirmAction(actionId: action.actionId)
            resolved = true
            resolvedStatus = res.message ?? "Confirmed"
            await onResolved()
        } catch {}
    }

    private func reject() async {
        do {
            _ = try await service.rejectAction(actionId: action.actionId)
            resolved = true
            resolvedStatus = "Rejected"
            await onResolved()
        } catch {}
    }
}
