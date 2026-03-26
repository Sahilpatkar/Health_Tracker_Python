import SwiftUI

private let muscleGroups = ["chest", "back", "legs", "shoulders", "arms", "core", "full_body"]
private let equipment = ["barbell", "dumbbell", "cable", "machine", "bodyweight", "kettlebell", "other"]

struct AdminExercisesView: View {
    @State private var exercises: [Exercise] = []
    @State private var search = ""
    @State private var newName = ""
    @State private var newMG = "chest"
    @State private var newEQ = "barbell"
    @State private var editId: Int?
    @State private var editName = ""
    @State private var editMG = ""
    @State private var editEQ = ""
    @State private var alert: AlertItem?

    private let service = ExerciseService()

    private var filtered: [Exercise] {
        if search.isEmpty { return exercises }
        return exercises.filter { $0.name.localizedCaseInsensitiveContains(search) }
    }

    var body: some View {
        List {
            addSection
            Section {
                ForEach(filtered) { ex in
                    if editId == ex.exerciseId {
                        editRow(ex)
                    } else {
                        exerciseRow(ex)
                    }
                }
            } header: {
                TextField("Search exercises...", text: $search)
                    .textFieldStyle(.roundedBorder)
                    .font(.subheadline)
            }
        }
        .navigationTitle("Exercise Catalog")
        .alert(item: $alert) { a in
            Alert(title: Text(a.title), message: Text(a.message), dismissButton: .default(Text("OK")))
        }
        .task { await load() }
        .refreshable { await load() }
    }

    private var addSection: some View {
        Section("Add New Exercise") {
            TextField("Name", text: $newName)
            Picker("Muscle Group", selection: $newMG) {
                ForEach(muscleGroups, id: \.self) { Text($0) }
            }
            Picker("Equipment", selection: $newEQ) {
                ForEach(equipment, id: \.self) { Text($0) }
            }
            Button("Add") {
                Task { await create() }
            }
            .disabled(newName.trimmingCharacters(in: .whitespaces).isEmpty)
        }
    }

    private func exerciseRow(_ ex: Exercise) -> some View {
        HStack {
            VStack(alignment: .leading) {
                Text(ex.name).font(.subheadline.bold())
                Text("\(ex.muscleGroup) · \(ex.equipment)")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Text(ex.isActive == true ? "Active" : "Inactive")
                .font(.caption2.bold())
                .foregroundStyle(ex.isActive == true ? .green : .red)
                .padding(.horizontal, 8).padding(.vertical, 3)
                .background(
                    (ex.isActive == true ? Color.green : Color.red).opacity(0.12),
                    in: Capsule()
                )
        }
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) {
                Task { await delete(ex.exerciseId) }
            } label: {
                Label("Delete", systemImage: "trash")
            }
            Button {
                editId = ex.exerciseId
                editName = ex.name
                editMG = ex.muscleGroup
                editEQ = ex.equipment
            } label: {
                Label("Edit", systemImage: "pencil")
            }
            .tint(.indigo)
        }
        .swipeActions(edge: .leading) {
            Button {
                Task { await toggle(ex) }
            } label: {
                Label(ex.isActive == true ? "Deactivate" : "Activate",
                      systemImage: ex.isActive == true ? "xmark" : "checkmark")
            }
            .tint(ex.isActive == true ? .orange : .green)
        }
    }

    private func editRow(_ ex: Exercise) -> some View {
        VStack(spacing: 8) {
            TextField("Name", text: $editName)
            Picker("Muscle Group", selection: $editMG) {
                ForEach(muscleGroups, id: \.self) { Text($0) }
            }
            Picker("Equipment", selection: $editEQ) {
                ForEach(equipment, id: \.self) { Text($0) }
            }
            HStack {
                Button("Save") {
                    Task { await update(ex.exerciseId) }
                }
                .buttonStyle(.borderedProminent).tint(.green)
                Button("Cancel") { editId = nil }
                    .buttonStyle(.bordered)
            }
        }
    }

    // MARK: - CRUD

    private func load() async {
        exercises = (try? await service.getAll()) ?? []
    }

    private func create() async {
        do {
            _ = try await service.create(CreateExerciseRequest(
                name: newName, muscleGroup: newMG, equipment: newEQ
            ))
            newName = ""
            await load()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }

    private func update(_ id: Int) async {
        do {
            _ = try await service.update(id: id, UpdateExerciseRequest(
                name: editName, muscleGroup: editMG, equipment: editEQ, isActive: nil
            ))
            editId = nil
            await load()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }

    private func delete(_ id: Int) async {
        do {
            try await service.delete(id: id)
            await load()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }

    private func toggle(_ ex: Exercise) async {
        _ = try? await service.update(id: ex.exerciseId, UpdateExerciseRequest(
            name: nil, muscleGroup: nil, equipment: nil, isActive: !(ex.isActive ?? true)
        ))
        await load()
    }
}
