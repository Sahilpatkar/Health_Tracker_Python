import SwiftUI

private let goalTypes = ["muscle_gain", "fat_loss", "recomposition"]

struct SettingsView: View {
    @State private var goalType = "fat_loss"
    @State private var calories: Double = 2000
    @State private var protein: Double = 120
    @State private var carbs: Double = 0
    @State private var fat: Double = 0
    @State private var trainingDays: Int = 4
    @State private var saved = false
    @State private var error: String?

    private let service = GoalService()

    var body: some View {
        Form {
            Section("Goal Type") {
                Picker("Goal", selection: $goalType) {
                    ForEach(goalTypes, id: \.self) { g in
                        Text(g.replacingOccurrences(of: "_", with: " ").capitalized)
                    }
                }
            }

            Section("Macro Targets") {
                numberRow("Daily Calories (kcal)", value: $calories)
                numberRow("Protein (g)", value: $protein)
                numberRow("Carbs (g)", value: $carbs)
                numberRow("Fat (g)", value: $fat)
            }

            Section("Training") {
                Stepper("Training Days / Week: \(trainingDays)", value: $trainingDays, in: 1...7)
            }

            if let error {
                Section {
                    Text(error).foregroundStyle(.red).font(.caption)
                }
            }

            Section {
                Button {
                    Task { await save() }
                } label: {
                    Text(saved ? "Saved!" : "Save Goals")
                        .fontWeight(.bold)
                        .frame(maxWidth: .infinity)
                }
                .listRowInsets(EdgeInsets())
                .buttonStyle(.borderedProminent)
                .tint(saved ? .green : .indigo)
                .clipShape(.rect(cornerRadius: 12))
                .padding()
            }
        }
        .navigationTitle("Goals & Settings")
        .task { await load() }
    }

    private func numberRow(_ label: String, value: Binding<Double>) -> some View {
        HStack {
            Text(label)
            Spacer()
            TextField("0", value: value, format: .number)
                .keyboardType(.decimalPad)
                .multilineTextAlignment(.trailing)
                .frame(width: 80)
        }
    }

    private func load() async {
        if let g = try? await service.get() {
            goalType = g.goalType
            calories = g.calorieTarget
            protein = g.proteinTarget
            carbs = g.carbTarget
            fat = g.fatTarget
            trainingDays = g.trainingDaysPerWeek
        }
    }

    private func save() async {
        do {
            _ = try await service.update(Goals(
                goalType: goalType,
                calorieTarget: calories,
                proteinTarget: protein,
                carbTarget: carbs,
                fatTarget: fat,
                trainingDaysPerWeek: trainingDays
            ))
            saved = true
            error = nil
            try? await Task.sleep(for: .seconds(2))
            saved = false
        } catch {
            self.error = error.localizedDescription
        }
    }
}
