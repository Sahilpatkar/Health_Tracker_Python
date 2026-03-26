import SwiftUI

struct ScoreGauge: View {
    let score: Double
    let label: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .stroke(color.opacity(0.2), lineWidth: 10)
                Circle()
                    .trim(from: 0, to: min(score / 100, 1.0))
                    .stroke(color, style: StrokeStyle(lineWidth: 10, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                    .animation(.easeOut(duration: 0.8), value: score)
                Text("\(Int(score))")
                    .font(.title2.bold().monospacedDigit())
            }
            .frame(width: 80, height: 80)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}
