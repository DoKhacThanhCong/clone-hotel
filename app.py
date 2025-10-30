from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)

# 🔹 Load dữ liệu khách sạn
hotels = pd.read_csv("hotels.csv")

# 🔹 File lưu đánh giá
REVIEWS_FILE = "reviews.csv"

# 🔹 Tạo file reviews.csv nếu chưa có
if not os.path.exists(REVIEWS_FILE):
    pd.DataFrame(columns=["hotel_name", "user", "rating", "comment"]).to_csv(REVIEWS_FILE, index=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    df = hotels.copy()

    if request.method == 'POST':
        city = request.form.get('location', '').lower()
        budget = float(request.form.get('budget', 999999999))
        stars = int(request.form.get('stars', 0))

        df = df[
            (df['city'].str.lower() == city) &
            (df['price'] <= budget) &
            (df['stars'] >= stars)
        ]

    else:
        sort = request.args.get('sort')
        stars = request.args.get('stars')
        buffet = request.args.get('buffet')
        pool = request.args.get('pool')
        sea = request.args.get('sea')
        view = request.args.get('view')

        if stars:
            df = df[df['stars'] >= int(stars)]
        if buffet:
            df = df[df['buffet'] == True]
        if pool:
            df = df[df['pool'] == True]
        if sea:
            df = df[df['sea'] == True]
        if view:
            df = df[df['view'] == True]

        if sort == 'asc':
            df = df.sort_values(by='price', ascending=True)
        elif sort == 'desc':
            df = df.sort_values(by='price', ascending=False)

    results = df.to_dict(orient='records')
    return render_template('result.html', hotels=results)


# 🔹 Chi tiết khách sạn + đánh giá
@app.route('/hotel/<name>', methods=['GET', 'POST'])
def hotel_detail(name):
    hotel = hotels[hotels['name'] == name].to_dict(orient='records')
    if not hotel:
        return "Không tìm thấy khách sạn này", 404
    hotel = hotel[0]

    # 🔸 Nếu khách gửi đánh giá (POST)
    if request.method == 'POST':
        user = request.form.get('user', 'Ẩn danh')
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '')

        new_review = pd.DataFrame([{
            "hotel_name": name,
            "user": user,
            "rating": rating,
            "comment": comment
        }])
        new_review.to_csv(REVIEWS_FILE, mode='a', header=False, index=False)
        return redirect(url_for('hotel_detail', name=name))

    # 🔹 Tải đánh giá từ file
    reviews = pd.read_csv(REVIEWS_FILE)
    hotel_reviews = reviews[reviews['hotel_name'] == name].to_dict(orient='records')

    # 🔹 Tính điểm trung bình nếu có đánh giá
    avg_rating = round(sum(r['rating'] for r in hotel_reviews) / len(hotel_reviews), 1) if hotel_reviews else None

    # 🔹 Tự động tạo mô tả review nếu thiếu
    if 'review' not in hotel or pd.isna(hotel['review']):
        if hotel['stars'] >= 5:
            hotel['review'] = "Một trong những khách sạn tốt nhất bạn có thể chọn, dịch vụ hoàn hảo và đẳng cấp."
        elif hotel['stars'] == 4:
            hotel['review'] = "Khách sạn rất ổn, sạch sẽ và phục vụ chu đáo."
        elif hotel['stars'] == 3:
            hotel['review'] = "Khách sạn tầm trung, phù hợp với chuyến công tác hoặc du lịch tiết kiệm."
        else:
            hotel['review'] = "Cơ sở vật chất cơ bản nhưng đủ tiện nghi cho kỳ nghỉ ngắn."

    return render_template('detail.html', hotel=hotel, reviews=hotel_reviews, avg_rating=avg_rating)


if __name__ == '__main__':
    app.run(debug=True)

