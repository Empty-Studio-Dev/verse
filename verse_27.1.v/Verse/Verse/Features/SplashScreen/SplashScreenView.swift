import SwiftUI

struct SplashScreenView: View {
    var body: some View {
        ZStack {
            Color.bacground
                .ignoresSafeArea(.all)
            Image(.logo)
                .resizable()
                .frame(width: 213.0, height: 213.0)
        }
    }
}

#Preview {
    SplashScreenView()
}
