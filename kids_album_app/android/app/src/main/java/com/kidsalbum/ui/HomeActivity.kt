package com.kidsalbum.ui

import android.os.Bundle
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.GridLayoutManager
import com.kidsalbum.R
import com.kidsalbum.adapter.PhotoAdapter
import com.kidsalbum.databinding.ActivityHomeBinding
import com.kidsalbum.model.Photo

class HomeActivity : AppCompatActivity() {

    private lateinit var binding: ActivityHomeBinding
    private lateinit var photoAdapter: PhotoAdapter
    private var currentCategory = "all"

    // 模拟数据
    private val allPhotos = listOf(
        Photo(1, "birthday", "3岁生日", "🎂", R.color.primary_pink),
        Photo(2, "travel", "去海边", "🏖️", R.color.primary_blue),
        Photo(3, "daily", "幼儿园", "🏫", R.color.primary_green),
        Photo(4, "birthday", "蛋糕", "🎂", R.color.primary_yellow),
        Photo(5, "travel", "爬山", "⛰️", R.color.primary_green),
        Photo(6, "daily", "画画", "🎨", R.color.primary_purple),
        Photo(7, "holiday", "春节", "🧧", R.color.primary_red),
        Photo(8, "travel", "游乐场", "🎢", R.color.primary_orange),
        Photo(9, "daily", "跳舞", "💃", R.color.primary_pink),
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityHomeBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupRecyclerView()
        setupCategoryTabs()
        setupBottomNav()
        setupFab()
        
        // 默认显示全部
        updatePhotos()
    }

    private fun setupRecyclerView() {
        photoAdapter = PhotoAdapter { photo ->
            // 点击照片的回调，可以跳转详情页
            Toast.makeText(this, "查看: ${photo.title}", Toast.LENGTH_SHORT).show()
        }

        binding.rvPhotos.apply {
            layoutManager = GridLayoutManager(this@HomeActivity, 3)
            adapter = photoAdapter
        }
    }

    private fun setupCategoryTabs() {
        // 分类点击事件
        val categoryViews = listOf(
            binding.tvCategoryAll to "all",
            binding.tvCategoryBirthday to "birthday",
            binding.tvCategoryTravel to "travel",
            binding.tvCategoryDaily to "daily",
            binding.tvCategoryHoliday to "holiday"
        )

        categoryViews.forEach { (view, category) ->
            view.setOnClickListener {
                currentCategory = category
                updateCategoryUI(view)
                updatePhotos()
            }
        }
        
        // 默认选中第一个
        updateCategoryUI(binding.tvCategoryAll)
    }

    private fun updateCategoryUI(selectedView: View) {
        // 重置所有分类状态
        val allViews = listOf(
            binding.tvCategoryAll,
            binding.tvCategoryBirthday,
            binding.tvCategoryTravel,
            binding.tvCategoryDaily,
            binding.tvCategoryHoliday
        )
        
        // 这里简化处理，实际应该用 selector
        // 选中状态在 XML 中定义，这里只需高亮选中的
        selectedView.alpha = 1.0f
        allViews.filter { it != selectedView }.forEach { it.alpha = 0.6f }
    }

    private fun updatePhotos() {
        val filtered = if (currentCategory == "all") {
            allPhotos
        } else {
            allPhotos.filter { it.category == currentCategory }
        }
        photoAdapter.submitList(filtered)
    }

    private fun setupBottomNav() {
        // 底部导航点击
        binding.navHome.setOnClickListener { }
        binding.navAlbum.setOnClickListener { 
            Toast.makeText(this, "相册功能开发中", Toast.LENGTH_SHORT).show()
        }
        binding.navUpload.setOnClickListener { 
            Toast.makeText(this, "上传功能开发中", Toast.LENGTH_SHORT).show()
        }
        binding.navProfile.setOnClickListener { 
            Toast.makeText(this, "个人中心开发中", Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupFab() {
        binding.fabCamera.setOnClickListener {
            Toast.makeText(this, "📷 拍照上传功能开发中...", Toast.LENGTH_SHORT).show()
        }
    }
}
