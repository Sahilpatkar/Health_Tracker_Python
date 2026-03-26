import SwiftUI
import Charts
import PhotosUI

struct BodyProgressView: View {
    @State private var date = Date()
    @State private var weight: Double = 0
    @State private var waist: Double = 0
    @State private var metrics: [BodyMetric] = []
    @State private var photos: [BodyPhoto] = []
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var fullscreenPhoto: BodyPhoto?
    @State private var alert: AlertItem?

    private let service = BodyService()
    private let dateFormatter: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f
    }()

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                logSection
                uploadSection
                if !metrics.isEmpty { weightChart }
                if !photos.isEmpty { photosGrid }
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Body Progress")
        .alert(item: $alert) { a in
            Alert(title: Text(a.title), message: Text(a.message), dismissButton: .default(Text("OK")))
        }
        .fullScreenCover(item: $fullscreenPhoto) { photo in
            photoFullscreen(photo)
        }
        .task { await load() }
        .refreshable { await load() }
        .onChange(of: selectedPhoto) { _, newVal in
            if let newVal { Task { await uploadPhoto(newVal) } }
        }
    }

    // MARK: - Sections

    private var logSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Log Weight / Waist").font(.headline)
            DatePicker("Date", selection: $date, displayedComponents: .date)
            HStack(spacing: 12) {
                VStack(alignment: .leading) {
                    Text("Weight (kg)").font(.caption).foregroundStyle(.secondary)
                    TextField("0", value: $weight, format: .number)
                        .keyboardType(.decimalPad)
                        .textFieldStyle(.roundedBorder)
                }
                VStack(alignment: .leading) {
                    Text("Waist (cm)").font(.caption).foregroundStyle(.secondary)
                    TextField("optional", value: $waist, format: .number)
                        .keyboardType(.decimalPad)
                        .textFieldStyle(.roundedBorder)
                }
            }
            Button {
                Task { await saveMetrics() }
            } label: {
                Text("Save Metrics").fontWeight(.semibold).frame(maxWidth: .infinity).padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent).tint(.indigo)
            .clipShape(.rect(cornerRadius: 12))
        }
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    private var uploadSection: some View {
        VStack(spacing: 12) {
            Image(systemName: "camera.fill")
                .font(.largeTitle)
                .foregroundStyle(.secondary)
            PhotosPicker(selection: $selectedPhoto, matching: .images) {
                Text("Choose or take photo")
                    .fontWeight(.semibold)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
            }
            .buttonStyle(.borderedProminent).tint(.indigo)
            .clipShape(.rect(cornerRadius: 12))
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.background, in: .rect(cornerRadius: 16))
    }

    @ViewBuilder
    private var weightChart: some View {
        DashboardCard(title: "Weight Trend") {
            Chart(metrics) { m in
                LineMark(
                    x: .value("Date", m.date),
                    y: .value("kg", m.weightKg)
                )
                .foregroundStyle(.indigo)
                PointMark(
                    x: .value("Date", m.date),
                    y: .value("kg", m.weightKg)
                )
                .foregroundStyle(.indigo)
            }
            .frame(height: 200)
        }
    }

    private var photosGrid: some View {
        DashboardCard(title: "Photos") {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 100), spacing: 8)], spacing: 8) {
                ForEach(photos) { photo in
                    photoCard(photo)
                }
            }
        }
    }

    @ViewBuilder
    private func photoCard(_ photo: BodyPhoto) -> some View {
        let url = AppConfig.mediaBaseURL.appendingPathComponent(photo.photoUrl)
        VStack(spacing: 4) {
            AsyncImage(url: url) { phase in
                switch phase {
                case .success(let image):
                    image.resizable().scaledToFill()
                        .frame(height: 120).clipped()
                case .failure:
                    Color.gray.overlay(Image(systemName: "photo").foregroundStyle(.white))
                default:
                    ProgressView().frame(height: 120)
                }
            }
            .frame(height: 120)
            .clipShape(.rect(cornerRadius: 10))
            .onTapGesture { fullscreenPhoto = photo }
            Text(photo.takenDate)
                .font(.caption2).foregroundStyle(.secondary)
        }
        .contextMenu {
            Button(role: .destructive) {
                Task { await deletePhoto(photo.photoId) }
            } label: {
                Label("Delete", systemImage: "trash")
            }
        }
    }

    private func photoFullscreen(_ photo: BodyPhoto) -> some View {
        let url = AppConfig.mediaBaseURL.appendingPathComponent(photo.photoUrl)
        return ZStack(alignment: .topTrailing) {
            Color.black.ignoresSafeArea()
            AsyncImage(url: url) { phase in
                if case .success(let img) = phase {
                    img.resizable().scaledToFit()
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            Button { fullscreenPhoto = nil } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.title)
                    .foregroundStyle(.white)
                    .padding()
            }
        }
    }

    // MARK: - Logic

    private func load() async {
        metrics = (try? await service.getMetrics()) ?? []
        photos = (try? await service.getPhotos()) ?? []
    }

    private func saveMetrics() async {
        guard weight > 0 else {
            alert = AlertItem(title: "Error", message: "Enter valid weight")
            return
        }
        do {
            _ = try await service.saveMetrics(SaveBodyMetricsRequest(
                date: dateFormatter.string(from: date),
                weightKg: weight,
                waistCm: waist > 0 ? waist : nil
            ))
            await load()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }

    private func uploadPhoto(_ item: PhotosPickerItem) async {
        guard let data = try? await item.loadTransferable(type: Data.self) else { return }
        do {
            _ = try await service.uploadPhoto(
                imageData: data,
                takenDate: dateFormatter.string(from: date),
                notes: nil
            )
            await load()
        } catch {
            alert = AlertItem(title: "Upload Failed", message: error.localizedDescription)
        }
        selectedPhoto = nil
    }

    private func deletePhoto(_ id: Int) async {
        do {
            try await service.deletePhoto(id: id)
            if fullscreenPhoto?.photoId == id { fullscreenPhoto = nil }
            await load()
        } catch {
            alert = AlertItem(title: "Error", message: error.localizedDescription)
        }
    }
}

