import SwiftUI

private let mealTypes = ["Breakfast", "Morning Snacks", "Lunch", "Evening Snacks", "Dinner"]

struct NutritionLogView: View {
    @State private var foodItems: [FoodItem] = []
    @State private var selectedId: Int?
    @State private var mealType = "Lunch"
    @State private var date = Date()
    @State private var quantity: Double = 1
    @State private var waterDate = Date()
    @State private var waterAmount: Double = 0.5
    @State private var recentIntake: [FoodIntakeRecord] = []
    @State private var alert: AlertItem?

    private let service = FoodService()
    private let dateFormatter: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f
    }()

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                foodSection
                waterSection
                recentSection
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Log Food & Water")
        .alert(item: $alert) { item in
            Alert(title: Text(item.title), message: Text(item.message), dismissButton: .default(Text("OK")))
        }
        .task { await load() }
    }

    // MARK: - Food

    private var foodSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Food Intake").font(.headline)
            DatePicker("Date", selection: $date, displayedComponents: .date)
            Picker("Meal Type", selection: $mealType) {
                ForEach(mealTypes, id: \.self) { Text($0) }
            }
            if !foodItems.isEmpty {
                Picker("Food Item", selection: $selectedId) {
                    ForEach(foodItems) { item in
                        Text(item.foodItem).tag(Optional(item.foodId))
                    }
                }
            }
            HStack {
                Text("Quantity")
                Spacer()
                TextField("1", value: $quantity, format: .number)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 80)
            }
            if let sel = foodItems.first(where: { $0.foodId == selectedId }) {
                Text("\(Int(sel.calories ?? 0)) kcal · \(Int(sel.protein ?? 0))g protein")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Button {
                Task { await addFood() }
            } label: {
                Text("Add Food").fontWeight(.semibold).frame(maxWidth: .infinity).padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent).tint(.indigo)
            .clipShape(.rect(cornerRadius: 12))
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    // MARK: - Water

    private var waterSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Water Intake", systemImage: "drop.fill")
                .font(.headline).foregroundStyle(.blue)
            DatePicker("Date", selection: $waterDate, displayedComponents: .date)
            HStack {
                Text("Litres")
                Spacer()
                TextField("0.5", value: $waterAmount, format: .number)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 80)
            }
            Button {
                Task { await addWater() }
            } label: {
                Text("Log Water").fontWeight(.semibold).frame(maxWidth: .infinity).padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent).tint(.blue)
            .clipShape(.rect(cornerRadius: 12))
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    // MARK: - Recent

    @ViewBuilder
    private var recentSection: some View {
        if !recentIntake.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                Text("Recent Entries (7 days)").font(.headline)
                ForEach(recentIntake.prefix(20)) { r in
                    HStack {
                        VStack(alignment: .leading) {
                            Text(r.foodItem).font(.subheadline)
                            Text("\(r.date) · \(r.mealType)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text("×\(r.quantity, specifier: "%.1f")")
                            .font(.caption.bold()).foregroundStyle(.secondary)
                    }
                    Divider()
                }
            }
            .padding()
            .background(.background, in: .rect(cornerRadius: 16))
        }
    }

    // MARK: - Actions

    private func load() async {
        foodItems = (try? await service.items()) ?? []
        if selectedId == nil { selectedId = foodItems.first?.foodId }
        recentIntake = (try? await service.getIntake(days: 7)) ?? []
    }

    private func addFood() async {
        guard let id = selectedId,
              let item = foodItems.first(where: { $0.foodId == id }),
              quantity > 0 else {
            alert = AlertItem(title: "Error", message: "Select item & quantity")
            return
        }
        do {
            _ = try await service.addIntake(AddFoodIntakeRequest(
                foodId: id, date: dateFormatter.string(from: date),
                mealType: mealType, foodItem: item.foodItem,
                quantity: quantity, unit: "serving"
            ))
            recentIntake = (try? await service.getIntake(days: 7)) ?? []
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }

    private func addWater() async {
        do {
            _ = try await service.addWater(AddWaterRequest(
                date: dateFormatter.string(from: waterDate),
                waterIntake: waterAmount
            ))
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }
}
