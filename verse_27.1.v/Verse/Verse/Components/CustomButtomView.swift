import SwiftUI

struct CustomButtomView: View {
    var title: String // текст кнопки
    var action: () -> Void // активный тригер когда кнопка нажата
    
    var body: some View {
        Button(action: action){
            Text(title)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.appButton)
                .foregroundStyle(Color.bacground)
                .cornerRadius(16)
        }
        
    }
}
