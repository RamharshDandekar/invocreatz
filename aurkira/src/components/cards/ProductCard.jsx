import Image from 'next/image';
import Link from 'next/link';

const ProductCard = ({ product }) => {
    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <Link href={`/shop/${product.id}`}>
                <div className="relative h-64">
                    <Image
                        src={product.imageUrl}
                        alt={product.name}
                        layout="fill"
                        objectFit="cover"
                    />
                </div>
                <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                        {product.name}
                    </h3>
                    <p className="text-gray-600">
                        ${product.price}
                    </p>
                </div>
            </Link>
        </div>
    );
};

export default ProductCard;