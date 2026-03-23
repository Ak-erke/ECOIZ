import SwiftUI

enum EcoTheme {
    static let primary = Color(hex: 0x58CC02)
    static let secondary = Color(hex: 0x89E219)
    static let sky = Color(hex: 0x1CB0F6)
    static let sun = Color(hex: 0xFFD95A)
    static let ink = Color(hex: 0x173100)
    static let card = Color.white.opacity(0.94)
    static let softBackgroundTop = Color(hex: 0xFFFFFF)
    static let softBackgroundBottom = Color(hex: 0xF8FAFC)
}

enum EcoTypography {
    static let largeTitle = Font.system(size: 34, weight: .bold, design: .rounded)
    static let title1 = Font.system(size: 28, weight: .bold, design: .rounded)
    static let title2 = Font.system(size: 22, weight: .semibold, design: .rounded)
    static let headline = Font.system(size: 17, weight: .semibold, design: .rounded)
    static let body = Font.system(size: 17, weight: .regular, design: .rounded)
    static let callout = Font.system(size: 16, weight: .medium, design: .rounded)
    static let subheadline = Font.system(size: 15, weight: .regular, design: .rounded)
    static let footnote = Font.system(size: 13, weight: .medium, design: .rounded)
    static let caption = Font.system(size: 12, weight: .medium, design: .rounded)
    static let metricXL = Font.system(size: 56, weight: .heavy, design: .rounded)
    static let metricL = Font.system(size: 48, weight: .heavy, design: .rounded)
    static let buttonPrimary = Font.system(size: 17, weight: .bold, design: .rounded)
    static let buttonSecondary = Font.system(size: 15, weight: .semibold, design: .rounded)
}

struct DuoPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(EcoTypography.buttonPrimary)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(
                        LinearGradient(
                            colors: [EcoTheme.primary, EcoTheme.secondary],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(.white.opacity(0.25), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .shadow(color: EcoTheme.primary.opacity(0.28), radius: 10, y: 6)
    }
}

struct DuoSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(EcoTypography.buttonSecondary)
            .foregroundStyle(EcoTheme.ink)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(Color.white.opacity(0.92))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color.black.opacity(0.08), lineWidth: 1)
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
    }
}

struct DuoCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(EcoTheme.card)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(EcoTheme.primary.opacity(0.16), lineWidth: 1)
            )
            .shadow(color: .black.opacity(0.06), radius: 12, y: 6)
    }
}

extension View {
    func duoCard() -> some View {
        modifier(DuoCardModifier())
    }
}

struct EcoBackground: View {
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [EcoTheme.softBackgroundTop, EcoTheme.softBackgroundBottom],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            Circle()
                .fill(Color.black.opacity(0.025))
                .frame(width: 260, height: 260)
                .offset(x: 150, y: -290)
            Circle()
                .fill(EcoTheme.primary.opacity(0.04))
                .frame(width: 240, height: 240)
                .offset(x: -150, y: 290)
        }
        .ignoresSafeArea()
    }
}

extension Color {
    init(hex: UInt32) {
        let r = Double((hex >> 16) & 0xFF) / 255.0
        let g = Double((hex >> 8) & 0xFF) / 255.0
        let b = Double(hex & 0xFF) / 255.0
        self.init(red: r, green: g, blue: b)
    }
}
