import Image from 'next/image';
import Link from 'next/link';

const CategoryCard = ({ category }) => {
    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <Link href={`/shop?category=${category.slug}`}> {/* Link to product listing page with category filter */}
                <div className="relative h-48">
                    <Image
                        src={category.imageUrl}
                        alt={category.name}
                        layout="fill"
                        objectFit="cover"
                    />
                </div>
                <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                        {category.name}
                    </h3>
                </div>
            </Link>
        </div>
    );
};

export default CategoryCard;