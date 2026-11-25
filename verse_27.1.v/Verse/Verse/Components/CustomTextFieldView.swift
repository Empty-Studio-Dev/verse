import SwiftUI

struct CustomTextFieldView: View {
    @Binding var text: String
    var placeholder: String
    
    var body: some View {
        TextField(placeholder, text: $text,
                  prompt:
                    Text(placeholder)
                        .foregroundColor(.appSecondDark)
        )
            .padding()
            .background {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.appGray)
            }
            .overlay {
                RoundedRectangle(cornerRadius: 16)
                    .stroke(Color.appSecond, lineWidth: 0.5)
            }
            
    }
}

