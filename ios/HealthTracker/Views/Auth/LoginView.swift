import SwiftUI

struct LoginView: View {
    @Environment(AuthStore.self) private var auth
    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var isRegister = false
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let service = AuthService()

    var body: some View {
        VStack(spacing: 0) {
            Spacer()
            VStack(spacing: 24) {
                VStack(spacing: 4) {
                    Text("Health Tracker")
                        .font(.largeTitle.bold())
                        .foregroundStyle(
                            LinearGradient(colors: [.indigo, .purple], startPoint: .leading, endPoint: .trailing)
                        )
                    Text(isRegister ? "Create your account" : "Sign in to continue")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                VStack(spacing: 16) {
                    TextField("Username", text: $username)
                        .textContentType(.username)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .padding()
                        .background(.quaternary, in: .rect(cornerRadius: 12))

                    SecureField("Password", text: $password)
                        .textContentType(isRegister ? .newPassword : .password)
                        .padding()
                        .background(.quaternary, in: .rect(cornerRadius: 12))

                    if isRegister {
                        SecureField("Confirm Password", text: $confirmPassword)
                            .textContentType(.newPassword)
                            .padding()
                            .background(.quaternary, in: .rect(cornerRadius: 12))
                    }
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(.red)
                }

                Button {
                    Task { await submit() }
                } label: {
                    Group {
                        if isLoading {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Text(isRegister ? "Register" : "Sign In")
                                .fontWeight(.semibold)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                }
                .buttonStyle(.borderedProminent)
                .tint(.indigo)
                .clipShape(.rect(cornerRadius: 12))
                .disabled(isLoading)

                Button {
                    withAnimation { isRegister.toggle() }
                    errorMessage = nil
                } label: {
                    Text(isRegister ? "Already have an account? **Sign In**" : "Don't have an account? **Register**")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(28)
            .background(.background, in: .rect(cornerRadius: 20))
            .shadow(color: .black.opacity(0.08), radius: 16, y: 8)
            .padding(.horizontal, 24)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }

    private func submit() async {
        guard !username.isEmpty, !password.isEmpty else {
            errorMessage = "Fill in all fields."
            return
        }
        if isRegister && password != confirmPassword {
            errorMessage = "Passwords do not match."
            return
        }
        isLoading = true
        errorMessage = nil
        do {
            if isRegister {
                _ = try await service.register(username: username, password: password)
                withAnimation { isRegister = false }
                errorMessage = nil
            } else {
                let response = try await service.login(username: username, password: password)
                auth.login(token: response.token, username: response.username, role: response.role)
            }
        } catch let err as APIError {
            errorMessage = err.errorDescription
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
