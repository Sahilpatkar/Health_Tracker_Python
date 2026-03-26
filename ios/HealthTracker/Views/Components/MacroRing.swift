import SwiftUI

struct MacroRing: View {
    let value: Double
    let target: Double
    let label: String
    let color: Color

    private var progress: Double {
        guard target > 0 else { return 0 }
        return min(value / target, 1.0)
    }

    var body: some View {
        VStack(spacing: 6) {
            ZStack {
                Circle()
                    .stroke(color.opacity(0.2), lineWidth: 8)
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(color, style: StrokeStyle(lineWidth: 8, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                    .animation(.easeOut(duration: 0.6), value: progress)
                VStack(spacing: 0) {
                    Text("\(Int(value))")
                        .font(.subheadline.bold().monospacedDigit())
                    Text("/ \(Int(target))")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(width: 72, height: 72)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }
}
