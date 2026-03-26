import SwiftUI

private let muscleGroups = ["All", "chest", "back", "legs", "shoulders", "arms", "core", "full_body"]

struct WorkoutLogView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var date = Date()
    @State private var notes = ""
    @State private var filter = "All"
    @State private var exercises: [Exercise] = []
    @State private var selectedId: Int?
    @State private var sets: [SetEntry] = [SetEntry()]
    @State private var sessionExercises: [SessionEntry] = []
    @State private var alert: AlertItem?

    private let exerciseService = ExerciseService()
    private let workoutService = WorkoutService()

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                dateAndNotesSection
                addExerciseSection
                if !sessionExercises.isEmpty {
                    currentSessionSection
                }
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Log Workout")
        .alert(item: $alert) { item in
            Alert(title: Text(item.title), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
        .task { await loadExercises() }
        .onChange(of: filter) { _, _ in
            Task { await loadExercises() }
        }
    }

    // MARK: - Sections

    private var dateAndNotesSection: some View {
        VStack(spacing: 12) {
            DatePicker("Date", selection: $date, displayedComponents: .date)
            TextField("Notes (optional)", text: $notes)
                .textFieldStyle(.roundedBorder)
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    private var addExerciseSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Add Exercise").font(.headline)
            HStack {
                Picker("Muscle Group", selection: $filter) {
                    ForEach(muscleGroups, id: \.self) { Text($0) }
                }
                .pickerStyle(.menu)
                Spacer()
                if !exercises.isEmpty {
                    Picker("Exercise", selection: $selectedId) {
                        ForEach(exercises) { ex in
                            Text(ex.name).tag(Optional(ex.exerciseId))
                        }
                    }
                    .pickerStyle(.menu)
                }
            }

            ForEach(sets.indices, id: \.self) { i in
                setRow(index: i)
            }

            Button {
                sets.append(SetEntry())
            } label: {
                Label("Add Set", systemImage: "plus")
                    .font(.subheadline.bold())
            }

            Button {
                addExerciseToSession()
            } label: {
                Text("Add Exercise to Session")
                    .fontWeight(.semibold)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent)
            .tint(.indigo)
            .clipShape(.rect(cornerRadius: 12))
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    @ViewBuilder
    private func setRow(index i: Int) -> some View {
        HStack(spacing: 8) {
            Text("\(i + 1)")
                .font(.caption.bold())
                .foregroundStyle(.secondary)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text("Weight").font(.caption2).foregroundStyle(.secondary)
                TextField("0", value: $sets[i].weight, format: .number)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("Reps").font(.caption2).foregroundStyle(.secondary)
                TextField("0", value: $sets[i].reps, format: .number)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("RPE").font(.caption2).foregroundStyle(.secondary)
                TextField("-", value: $sets[i].rpe, format: .number)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text("RIR").font(.caption2).foregroundStyle(.secondary)
                TextField("-", value: $sets[i].rir, format: .number)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
            }
            Button(role: .destructive) {
                if sets.count > 1 { sets.remove(at: i) }
            } label: {
                Image(systemName: "trash")
                    .font(.caption)
            }
        }
    }

    private var currentSessionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Current Session").font(.headline)
            ForEach(sessionExercises.indices, id: \.self) { i in
                HStack {
                    VStack(alignment: .leading) {
                        Text(sessionExercises[i].name).font(.subheadline.bold())
                        Text("\(sessionExercises[i].sets.count) sets")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button(role: .destructive) {
                        sessionExercises.remove(at: i)
                    } label: {
                        Image(systemName: "trash").font(.caption)
                    }
                }
                .padding(12)
                .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 12))
            }

            Button {
                Task { await finishWorkout() }
            } label: {
                Label("Finish & Save Workout", systemImage: "checkmark.circle.fill")
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
            .tint(.green)
            .clipShape(.rect(cornerRadius: 12))
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    // MARK: - Logic

    private func loadExercises() async {
        let mg = filter == "All" ? nil : filter
        exercises = (try? await exerciseService.getActive(muscleGroup: mg)) ?? []
        if selectedId == nil || !exercises.contains(where: { $0.exerciseId == selectedId }) {
            selectedId = exercises.first?.exerciseId
        }
    }

    private func addExerciseToSession() {
        guard let id = selectedId,
              let ex = exercises.first(where: { $0.exerciseId == id }) else { return }
        let validSets = sets.filter { $0.reps > 0 }
        guard !validSets.isEmpty else {
            alert = AlertItem(title: "Error", message: "Add at least one set with reps > 0")
            return
        }
        sessionExercises.append(SessionEntry(
            exerciseId: ex.exerciseId,
            name: ex.name,
            muscleGroup: ex.muscleGroup,
            sets: validSets
        ))
        sets = [SetEntry()]
    }

    private func finishWorkout() async {
        guard !sessionExercises.isEmpty else {
            alert = AlertItem(title: "Error", message: "Add at least one exercise")
            return
        }
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let req = SaveWorkoutRequest(
            sessionDate: formatter.string(from: date),
            notes: notes.isEmpty ? nil : notes,
            exercises: sessionExercises.map { entry in
                WorkoutExerciseEntry(
                    exerciseId: entry.exerciseId,
                    sets: entry.sets.map { s in
                        WorkoutSet(reps: s.reps, weight: s.weight, rpe: s.rpe, rir: s.rir)
                    }
                )
            }
        )
        do {
            _ = try await workoutService.save(req)
            dismiss()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }
}

// MARK: - Local models

private struct SetEntry {
    var reps: Int = 0
    var weight: Double = 0
    var rpe: Double?
    var rir: Double?
}

private struct SessionEntry {
    let exerciseId: Int
    let name: String
    let muscleGroup: String
    let sets: [SetEntry]
}

struct AlertItem: Identifiable {
    let id = UUID()
    let title: String
    let message: String
}
