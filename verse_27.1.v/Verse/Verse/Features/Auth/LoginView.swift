import SwiftUI

struct LoginView: View {
    @State private var showSplash = true
    @State private var emailText = ""
    
    var body: some View {
        ZStack {
            if showSplash {
                SplashScreenView()
                    .transition(.opacity)
                    .animation(.easeOut(duration: 1.5))
            } else {
                VStack {
//                    Component for Input
//                    CustomTextFieldView(text: $emailText, placeholder: "Email...")
                    CustomButtomView(title: "Send") {}
                }
                
            }
        }
        .onAppear {
            DispatchQueue.main
                .asyncAfter(deadline: .now() + 3) {
                    withAnimation {
                        self.showSplash = false
                    }
                }
        }
        
    }
    
}

#Preview {
    LoginView()
}
