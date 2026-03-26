import SwiftUI

struct MessageBubble: View {
    let role: String
    let content: String
    var isStreaming: Bool = false

    private var isUser: Bool { role == "user" }

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            if !isUser {
                Image(systemName: "brain.head.profile")
                    .font(.caption)
                    .padding(6)
                    .background(.green.opacity(0.15), in: Circle())
            }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(content.isEmpty && isStreaming ? "..." : content)
                    .font(.subheadline)
                    .textSelection(.enabled)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        isUser ? Color.indigo : Color(.secondarySystemGroupedBackground),
                        in: .rect(cornerRadii: .init(
                            topLeading: 16, bottomLeading: isUser ? 16 : 4,
                            bottomTrailing: isUser ? 4 : 16, topTrailing: 16
                        ))
                    )
                    .foregroundStyle(isUser ? .white : .primary)
            }
        }
        .padding(.leading, isUser ? 40 : 0)
        .padding(.trailing, isUser ? 0 : 40)
    }
}
