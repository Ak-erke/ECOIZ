import SwiftUI
import UIKit

enum EcoTheme {
    static let primary = Color(hex: 0x58CC02)
    static let secondary = Color(hex: 0x89E219)
    static let sky = Color(hex: 0x1CB0F6)
    static let sun = Color(hex: 0xFFD95A)
    static let ink = Color(dynamicLight: UIColor(red: 0.09, green: 0.19, blue: 0.00, alpha: 1), dark: UIColor(red: 0.93, green: 0.97, blue: 0.90, alpha: 1))
    static let secondaryText = Color(dynamicLight: UIColor.secondaryLabel, dark: UIColor(red: 0.72, green: 0.78, blue: 0.72, alpha: 1))
    static let card = Color(dynamicLight: UIColor.white.withAlphaComponent(0.94), dark: UIColor(red: 0.10, green: 0.14, blue: 0.10, alpha: 0.94))
    static let elevatedCard = Color(dynamicLight: UIColor.white.withAlphaComponent(0.98), dark: UIColor(red: 0.14, green: 0.18, blue: 0.14, alpha: 0.98))
    static let softBackgroundTop = Color(dynamicLight: UIColor(red: 1.00, green: 1.00, blue: 1.00, alpha: 1), dark: UIColor(red: 0.05, green: 0.08, blue: 0.06, alpha: 1))
    static let softBackgroundBottom = Color(dynamicLight: UIColor(red: 0.97, green: 0.98, blue: 0.99, alpha: 1), dark: UIColor(red: 0.08, green: 0.11, blue: 0.09, alpha: 1))
    static let surfaceStroke = Color(dynamicLight: UIColor.black.withAlphaComponent(0.08), dark: UIColor.white.withAlphaComponent(0.12))
    static let softStroke = Color(dynamicLight: UIColor.white.withAlphaComponent(0.58), dark: UIColor.white.withAlphaComponent(0.10))
    static let shadow = Color(dynamicLight: UIColor.black.withAlphaComponent(0.10), dark: UIColor.black.withAlphaComponent(0.28))
    static let fieldBackground = Color(dynamicLight: UIColor.white.withAlphaComponent(0.95), dark: UIColor(red: 0.16, green: 0.20, blue: 0.16, alpha: 0.95))
    static let avatarFill = Color(dynamicLight: UIColor(red: 0.07, green: 0.07, blue: 0.07, alpha: 1), dark: UIColor(red: 0.20, green: 0.24, blue: 0.20, alpha: 1))
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
                    .fill(EcoTheme.elevatedCard)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(EcoTheme.surfaceStroke, lineWidth: 1)
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
            .shadow(color: EcoTheme.shadow.opacity(0.6), radius: 12, y: 6)
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
                .fill(EcoTheme.shadow.opacity(0.18))
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

    init(dynamicLight: UIColor, dark: UIColor) {
        self.init(
            UIColor { traitCollection in
                traitCollection.userInterfaceStyle == .dark ? dark : dynamicLight
            }
        )
    }
}
